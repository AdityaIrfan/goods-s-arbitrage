import pytest
import pandas as pd

from src.storage import silver, gold
from src.storage.paths import data_path
from src.analyze.analyze import analyze_listings

SUBJECT = "minyak goreng test"


def _silver_row(**overrides) -> dict:
    base = {
        "id": "s1",
        "bronze_id": "b1",
        "brand": "bimoli",
        "product_type": "minyak goreng kemasan",
        "price_raw": 35000.0,
        "price_per_liter": 17000.0,
        "unit_original": "liter",
        "quantity_per_unit": 2.0,
        "min_order": None,
        "city": "Surabaya",
        "province": None,
        "delivery_coverage": None,
        "parsed_at": "2026-06-11T00:00:00+00:00",
        "parse_confidence": "high",
    }
    base.update(overrides)
    return base


@pytest.fixture
def bronze_data() -> pd.DataFrame:
    return pd.DataFrame([
        {"id": "b1", "source": "facebook", "scraped_at": "2026-06-08T09:12:00"},
        {"id": "b2", "source": "facebook", "scraped_at": "2026-06-08T14:40:00"},
        {"id": "b3", "source": "facebook", "scraped_at": "2026-06-08T10:00:00"},
        {"id": "b4", "source": "tokopedia_grosir", "scraped_at": "2026-06-09T08:00:00"},
    ])


@pytest.fixture
def silver_data() -> pd.DataFrame:
    return silver.silver_schema.validate(pd.DataFrame([
        _silver_row(id="s1", bronze_id="b1", price_per_liter=17000.0, city="Surabaya"),
        _silver_row(id="s2", bronze_id="b3", price_per_liter=19000.0, city="Surabaya"),
        _silver_row(id="s3", bronze_id="b2", price_per_liter=14000.0, city="Sidoarjo"),
        _silver_row(id="s4", bronze_id="b4", brand="sania", price_per_liter=15000.0, city="Jakarta"),
        _silver_row(id="s5", bronze_id="b1", brand="curah", product_type="minyak goreng curah", price_per_liter=None, city=None),
    ]))


@pytest.fixture
def cleanup_gold_files():
    yield
    data_path("gold", gold._price_spread_filename(SUBJECT)).unlink(missing_ok=True)
    data_path("gold", gold._opportunity_pairs_filename(SUBJECT)).unlink(missing_ok=True)
    data_path("gold", gold._brand_summary_filename(SUBJECT)).unlink(missing_ok=True)


def test_analyze_listings(silver_data, bronze_data, cleanup_gold_files):
    result = analyze_listings(silver_data, bronze_data, SUBJECT)

    assert result["price_spread_rows"] == 3
    assert result["opportunity_pairs_rows"] == 1
    assert result["brand_summary_rows"] == 2


def test_price_spread_aggregates_min_max_avg_count(silver_data, bronze_data, cleanup_gold_files):
    analyze_listings(silver_data, bronze_data, SUBJECT)

    spread = gold.get_price_spread(SUBJECT)
    row = spread[
        (spread["brand"] == "bimoli") & (spread["city"] == "Surabaya")
    ].iloc[0]

    assert row["product_type"] == "minyak goreng kemasan"
    assert row["date"] == "2026-06-08"
    assert row["source"] == "facebook"
    assert row["min_price_per_liter"] == pytest.approx(17000.0)
    assert row["max_price_per_liter"] == pytest.approx(19000.0)
    assert row["avg_price_per_liter"] == pytest.approx(18000.0)
    assert row["listing_count"] == 2
    assert row["lowest_price_silver_id"] == "s1"
    assert row["lowest_price_bronze_id"] == "b1"
    assert row["highest_price_silver_id"] == "s2"
    assert row["highest_price_bronze_id"] == "b3"
    assert list(row["silver_ids"]) == ["s1", "s2"]
    assert list(row["bronze_ids"]) == ["b1", "b3"]

    # row with null price_per_liter (s5) is excluded entirely
    assert not (spread["brand"] == "curah").any()


def test_opportunity_pair_finds_cheap_and_expensive_city(silver_data, bronze_data, cleanup_gold_files):
    analyze_listings(silver_data, bronze_data, SUBJECT)

    pairs = gold.get_opportunity_pairs(SUBJECT)
    assert len(pairs) == 1

    row = pairs.iloc[0]
    assert row["product_type"] == "minyak goreng kemasan"
    assert row["brand"] == "bimoli"
    assert row["date"] == "2026-06-08"
    assert row["cheap_city"] == "Sidoarjo"
    assert row["cheap_price_per_liter"] == pytest.approx(14000.0)
    assert row["expensive_city"] == "Surabaya"
    assert row["expensive_price_per_liter"] == pytest.approx(19000.0)
    assert row["price_diff_per_liter"] == pytest.approx(5000.0)
    assert row["estimated_shipping_per_liter"] == pytest.approx(1500.0)
    assert row["net_diff_per_liter"] == pytest.approx(3500.0)
    assert row["lowest_price_silver_id"] == "s3"
    assert row["lowest_price_bronze_id"] == "b2"
    assert row["highest_price_silver_id"] == "s2"
    assert row["highest_price_bronze_id"] == "b3"
    assert list(row["silver_ids"]) == ["s1", "s2", "s3"]
    assert list(row["bronze_ids"]) == ["b1", "b2", "b3"]


def test_single_city_group_has_no_opportunity_pair(silver_data, bronze_data, cleanup_gold_files):
    analyze_listings(silver_data, bronze_data, SUBJECT)

    pairs = gold.get_opportunity_pairs(SUBJECT)
    assert not (pairs["brand"] == "sania").any()


def test_brand_summary_groups_across_cities(silver_data, bronze_data, cleanup_gold_files):
    analyze_listings(silver_data, bronze_data, SUBJECT)

    summary = gold.get_brand_summary(SUBJECT)
    bimoli_row = summary[summary["brand"] == "bimoli"].iloc[0]

    assert bimoli_row["min_price_per_liter"] == pytest.approx(14000.0)
    assert bimoli_row["max_price_per_liter"] == pytest.approx(19000.0)
    assert bimoli_row["avg_price_per_liter"] == pytest.approx(16666.6667, abs=0.01)
    assert bimoli_row["city_count"] == 2
    assert bimoli_row["listing_count"] == 3
    assert bimoli_row["lowest_price_silver_id"] == "s3"
    assert bimoli_row["lowest_price_bronze_id"] == "b2"
    assert bimoli_row["highest_price_silver_id"] == "s2"
    assert bimoli_row["highest_price_bronze_id"] == "b3"
    assert list(bimoli_row["silver_ids"]) == ["s1", "s2", "s3"]
    assert list(bimoli_row["bronze_ids"]) == ["b1", "b2", "b3"]

    sania_row = summary[summary["brand"] == "sania"].iloc[0]
    assert sania_row["city_count"] == 1
    assert sania_row["listing_count"] == 1
    assert sania_row["lowest_price_silver_id"] == "s4"
    assert sania_row["highest_price_silver_id"] == "s4"
    assert list(sania_row["silver_ids"]) == ["s4"]
    assert list(sania_row["bronze_ids"]) == ["b4"]
