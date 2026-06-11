import difflib
from typing import Optional

import pandas as pd

# threshold kemiripan raw_text buat dianggap near-duplicate (0-1, makin tinggi makin ketat)
_FUZZY_THRESHOLD = 0.92


def deduplicate(bronze_data: pd.DataFrame, date_range: Optional[tuple[str, str]] = None) -> pd.DataFrame:
    """
    Tandai baris bronze yang duplikat dari baris bronze lain.
    - Exact: source + source_id sama
    - Near-duplicate: raw_text mirip (rasio >= _FUZZY_THRESHOLD)

    date_range (start, end) membatasi window scraped_at yang dicek; baris di luar
    window ditandai dedup_status="pending" (belum dicek) dan dianggap belum "ready".
    """
    data = bronze_data.copy()
    data["dedup_status"] = "ready"
    data["is_duplicate"] = False
    data["duplicate_of"] = None

    if date_range is not None:
        start, end = date_range
        in_range = data["scraped_at"].between(start, end)
        data.loc[~in_range, "dedup_status"] = "pending"

    eligible = data[data["dedup_status"] == "ready"].sort_values("scraped_at")

    seen_keys: dict[tuple[str, str], str] = {}
    seen_texts: list[tuple[str, str]] = []

    for idx, row in eligible.iterrows():
        source_key = (row["source"], row["source_id"])

        if row["source_id"] is not None and source_key in seen_keys:
            data.at[idx, "is_duplicate"] = True
            data.at[idx, "duplicate_of"] = seen_keys[source_key]
            continue

        duplicate_of = next(
            (
                seen_id for seen_id, seen_text in seen_texts
                if difflib.SequenceMatcher(None, row["raw_text"], seen_text).ratio() >= _FUZZY_THRESHOLD
            ),
            None,
        )

        if duplicate_of is not None:
            data.at[idx, "is_duplicate"] = True
            data.at[idx, "duplicate_of"] = duplicate_of
            continue

        if row["source_id"] is not None:
            seen_keys[source_key] = row["id"]
        seen_texts.append((row["id"], row["raw_text"]))

    return data
