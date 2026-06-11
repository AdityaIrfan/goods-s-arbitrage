import pytest
import pandas as pd

from src.storage import silver
from src.storage.paths import data_path
from src.load.load import load_listings

SUBJECT = "minyak goreng test"


def _validated_item(**overrides) -> dict:
    base = {
        "id": "s1",
        "bronze_id": "b1",
        "price": 32000.0,
        "currency": "IDR",
        "unit-quantity": {"liter": 2.0},
        "location": "Gresik",
        "brand": "fortune",
        "parse_confidence": "high",
        "unit_conversion_incomplete": False,
        "price_per_liter": 16000.0,
        "flag_reasons": [],
        "is_flagged": False,
    }
    base.update(overrides)
    return base


@pytest.fixture
def cleanup_silver_files():
    yield
    data_path("silver", silver._filename(SUBJECT)).unlink(missing_ok=True)
    data_path("silver", silver._pending_filename(SUBJECT)).unlink(missing_ok=True)


def test_high_confidence_unflagged_goes_to_approved(cleanup_silver_files):
    result = load_listings([_validated_item()], SUBJECT)

    assert result["approved"] == 1
    assert result["pending"] == 0

    approved = silver.get(SUBJECT)
    assert len(approved) == 1
    row = approved.iloc[0]
    assert row["id"] == "s1"
    assert row["bronze_id"] == "b1"
    assert row["brand"] == "fortune"
    assert row["product_type"] == "minyak goreng test kemasan"
    assert row["price_raw"] == 32000.0
    assert row["price_per_liter"] == 16000.0
    assert row["unit_original"] == "liter"
    assert row["quantity_per_unit"] == 2.0
    assert row["city"] == "Gresik"
    assert row["parse_confidence"] == "high"

    pending = silver.get_pending(SUBJECT)
    assert len(pending) == 0


def test_flagged_item_goes_to_pending_with_reasons(cleanup_silver_files):
    item = _validated_item(
        price_per_liter=100000.0,
        is_flagged=True,
        flag_reasons=["price_per_liter_out_of_range"],
    )

    result = load_listings([item], SUBJECT)

    assert result["approved"] == 0
    assert result["pending"] == 1

    pending = silver.get_pending(SUBJECT)
    assert len(pending) == 1
    row = pending.iloc[0]
    assert row["review_status"] == "pending"
    assert row["flag_reasons"] == ["price_per_liter_out_of_range"]


def test_low_confidence_goes_to_pending_even_without_flags(cleanup_silver_files):
    item = _validated_item(parse_confidence="low")

    result = load_listings([item], SUBJECT)

    assert result["approved"] == 0
    assert result["pending"] == 1


def test_curah_brand_uses_curah_product_type(cleanup_silver_files):
    item = _validated_item(brand="curah")

    load_listings([item], SUBJECT)

    approved = silver.get(SUBJECT)
    assert approved.iloc[0]["product_type"] == "minyak goreng test curah"


def test_unknown_brand_has_null_product_type(cleanup_silver_files):
    item = _validated_item(brand=None, parse_confidence="low")

    load_listings([item], SUBJECT)

    pending = silver.get_pending(SUBJECT)
    assert pd.isna(pending.iloc[0]["product_type"])


def test_nested_packaging_unit_original_and_quantity(cleanup_silver_files):
    item = _validated_item(
        price=198000.0,
        price_per_liter=16500.0,
        **{"unit-quantity": {"liter": 2.0, "karton": 1.0, "botol": 6.0}},
    )

    load_listings([item], SUBJECT)

    approved = silver.get(SUBJECT)
    row = approved.iloc[0]
    assert row["unit_original"] == "karton"
    assert row["quantity_per_unit"] == pytest.approx(12.0)


def test_dedup_filters_out_duplicate_bronze_ids(cleanup_silver_files):
    items = [
        _validated_item(id="s1", bronze_id="b1"),
        _validated_item(id="s2", bronze_id="b2"),
    ]
    dedup_data = pd.DataFrame([
        {"id": "b1", "dedup_status": "ready", "is_duplicate": False},
        {"id": "b2", "dedup_status": "ready", "is_duplicate": True},
    ])

    result = load_listings(items, SUBJECT, dedup_data)

    assert result["approved"] == 1
    approved = silver.get(SUBJECT)
    assert approved.iloc[0]["bronze_id"] == "b1"
