import pytest

from src.normalize.normalize import normalize_listings

SUBJECT = "minyak goreng"


def test_simple_liter_item_converts_price_per_liter_and_brand_case():
    parsed = [{
        "id": "s1",
        "bronze_id": "b1",
        "price": 32000.0,
        "currency": "IDR",
        "unit-quantity": {"liter": 2.0},
        "location": "Gresik",
        "brand": "Fortune",
        "parse_confidence": "high",
    }]

    result = normalize_listings(parsed, SUBJECT)

    assert result[0]["brand"] == "fortune"
    assert result[0]["price_per_liter"] == 16000.0
    assert result[0]["unit_conversion_incomplete"] is False
    assert result[0]["parse_confidence"] == "high"


def test_nested_packaging_multiplies_to_total_liter():
    parsed = [{
        "id": "s2",
        "bronze_id": "b2",
        "price": 198000.0,
        "currency": "IDR",
        "unit-quantity": {"liter": 2.0, "karton": 1.0, "botol": 6.0},
        "location": "Malang",
        "brand": "Bimoli",
        "parse_confidence": "high",
    }]

    result = normalize_listings(parsed, SUBJECT)

    assert result[0]["price_per_liter"] == pytest.approx(16500.0)
    assert result[0]["unit_conversion_incomplete"] is False


def test_kg_unit_uses_configured_conversion_factor():
    parsed = [{
        "id": "s3",
        "bronze_id": "b3",
        "price": 16000.0,
        "currency": "IDR",
        "unit-quantity": {"kg": 1.0},
        "location": "Jogja",
        "brand": "Curah",
        "parse_confidence": "high",
    }]

    result = normalize_listings(parsed, SUBJECT)

    assert result[0]["price_per_liter"] == pytest.approx(16000 / 1.087)
    assert result[0]["unit_conversion_incomplete"] is False


def test_unrecognized_unit_flags_incomplete_and_downgrades_confidence():
    parsed = [{
        "id": "s4",
        "bronze_id": "b4",
        "price": 100000.0,
        "currency": "IDR",
        "unit-quantity": {"karton": 10.0},
        "location": "Surabaya",
        "brand": "Sania",
        "parse_confidence": "high",
    }]

    result = normalize_listings(parsed, SUBJECT)

    assert result[0]["price_per_liter"] is None
    assert result[0]["unit_conversion_incomplete"] is True
    assert result[0]["parse_confidence"] == "medium"


def test_empty_unit_quantity_flags_incomplete_without_downgrading_below_low():
    parsed = [{
        "id": "s5",
        "bronze_id": "b5",
        "price": None,
        "currency": "IDR",
        "unit-quantity": {},
        "location": "Surabaya",
        "brand": "Bimoli",
        "parse_confidence": "low",
    }]

    result = normalize_listings(parsed, SUBJECT)

    assert result[0]["price_per_liter"] is None
    assert result[0]["unit_conversion_incomplete"] is True
    assert result[0]["parse_confidence"] == "low"


def test_brand_none_stays_none():
    parsed = [{
        "id": "s6",
        "bronze_id": "b6",
        "price": 16000.0,
        "currency": "IDR",
        "unit-quantity": {"liter": 1.0},
        "location": "Surabaya",
        "brand": None,
        "parse_confidence": "medium",
    }]

    result = normalize_listings(parsed, SUBJECT)

    assert result[0]["brand"] is None
