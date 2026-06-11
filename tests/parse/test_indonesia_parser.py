import pandas as pd

from src.parse.parser import parse_raw_text

SUBJECT = "minyak goreng"
LANG = "indonesia"
FORMATS = ["price", "currency", "unit-quantity", "location", "brand"]


def _parse_one(bronze_id: str, raw_text: str) -> list[dict]:
    data = pd.DataFrame([{"id": bronze_id, "raw_text": raw_text}])
    return parse_raw_text(FORMATS, data, LANG, SUBJECT)


def test_single_item_high_confidence():
    result = _parse_one(
        "b1",
        "Jual Minyak Goreng Bimoli 2L, harga 35rb per pcs. Ready stock area Surabaya",
    )

    assert len(result) == 1
    item = result[0]
    assert item["bronze_id"] == "b1"
    assert item["price"] == 35000.0
    assert item["currency"] == "IDR"
    assert item["unit-quantity"] == {"liter": 2.0}
    assert item["brand"] == "Bimoli"
    assert item["location"] == "Surabaya"
    assert item["parse_confidence"] == "high"


def test_decimal_price_with_rb_suffix():
    result = _parse_one("b2", "Bimoli 1 liter = 18.5rb, area Mojokerto")

    assert result[0]["price"] == 18500.0


def test_thousand_separator_price():
    result = _parse_one("b3", "Minyak Goreng Curah 5 Liter - Rp 95.000 - Lokasi: Mojokerto")

    assert result[0]["price"] == 95000.0


def test_multi_item_post_splits_into_multiple_rows_sharing_bronze_id():
    result = _parse_one(
        "b4",
        "Promo akhir bulan! Minyak goreng Fortune 2 liter 32rb, Tropical 2 liter 33rb, Filma 1 liter 17rb. Semua ready di Gresik",
    )

    assert len(result) == 3
    assert all(item["bronze_id"] == "b4" for item in result)

    by_brand = {item["brand"]: item for item in result}
    assert by_brand["Fortune"]["price"] == 32000.0
    assert by_brand["Tropical"]["price"] == 33000.0
    assert by_brand["Filma"]["price"] == 17000.0
    assert all(item["location"] == "Gresik" for item in result)
    assert all(item["unit-quantity"] == {"liter": 2.0} or item["unit-quantity"] == {"liter": 1.0} for item in result)
    assert all(item["parse_confidence"] == "high" for item in result)


def test_missing_location_yields_medium_confidence():
    result = _parse_one(
        "b5",
        "Distributor Minyak Goreng Fortune 2 Liter, kemasan 1 dus isi 6 pcs, harga Rp 195.000/dus, area pengiriman Jawa Timur",
    )

    assert len(result) == 1
    assert result[0]["location"] is None
    assert result[0]["parse_confidence"] == "medium"


def test_missing_price_yields_low_confidence():
    result = _parse_one("b6", "Minyak goreng Bimoli 2 liter tersedia di Surabaya, harga nego")

    assert result[0]["price"] is None
    assert result[0]["parse_confidence"] == "low"
