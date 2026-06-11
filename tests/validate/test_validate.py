from src.validate.validate import validate_listings

SUBJECT = "minyak goreng"


def _item(**overrides) -> dict:
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
    }
    base.update(overrides)
    return base


def test_within_range_is_not_flagged():
    result = validate_listings([_item()], SUBJECT)

    assert result[0]["is_flagged"] is False
    assert result[0]["flag_reasons"] == []


def test_price_per_liter_too_low_is_flagged():
    result = validate_listings([_item(price=2000.0, price_per_liter=1000.0)], SUBJECT)

    assert result[0]["is_flagged"] is True
    assert result[0]["flag_reasons"] == ["price_per_liter_out_of_range"]


def test_price_per_liter_too_high_is_flagged():
    result = validate_listings([_item(price=200000.0, price_per_liter=100000.0)], SUBJECT)

    assert result[0]["is_flagged"] is True
    assert result[0]["flag_reasons"] == ["price_per_liter_out_of_range"]


def test_unit_conversion_incomplete_is_flagged():
    result = validate_listings(
        [_item(unit_conversion_incomplete=True, unit_quantity={"karton": 10.0}, price_per_liter=None)],
        SUBJECT,
    )

    assert result[0]["is_flagged"] is True
    assert "unit_conversion_incomplete" in result[0]["flag_reasons"]


def test_missing_price_is_flagged():
    result = validate_listings(
        [_item(price=None, price_per_liter=None, parse_confidence="low")],
        SUBJECT,
    )

    assert result[0]["is_flagged"] is True
    assert "price_missing" in result[0]["flag_reasons"]


def test_missing_location_is_not_flagged():
    result = validate_listings([_item(location=None)], SUBJECT)

    assert result[0]["is_flagged"] is False
    assert result[0]["flag_reasons"] == []


def test_multiple_reasons_combine():
    result = validate_listings(
        [_item(price=None, price_per_liter=None, unit_conversion_incomplete=True)],
        SUBJECT,
    )

    assert result[0]["is_flagged"] is True
    assert set(result[0]["flag_reasons"]) == {"price_missing", "unit_conversion_incomplete"}
