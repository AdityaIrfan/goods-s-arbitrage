import pytest
import pandas as pd
from src.storage import gold
from src.storage.paths import data_path
from pandas.testing import assert_frame_equal


@pytest.fixture
def test_subject() -> str:
    return "minyak goreng test"


@pytest.fixture
def cleanup_test_files(test_subject):
    yield
    data_path("gold", gold._price_spread_filename(test_subject)).unlink(missing_ok=True)
    data_path("gold", gold._opportunity_pairs_filename(test_subject)).unlink(missing_ok=True)
    data_path("gold", gold._brand_summary_filename(test_subject)).unlink(missing_ok=True)


@pytest.fixture
def valid_price_spread_dataframe() -> pd.DataFrame:
    df = pd.DataFrame([
        {
            "product_type": "minyak goreng kemasan",
            "brand": "bimoli",
            "city": "Surabaya",
            "date": "2026-06-08",
            "source": "facebook",
            "min_price_per_liter": 17500.0,
            "max_price_per_liter": 17500.0,
            "avg_price_per_liter": 17500.0,
            "listing_count": 1,
            "lowest_price_silver_id": "s1",
            "lowest_price_bronze_id": "b1",
            "highest_price_silver_id": "s1",
            "highest_price_bronze_id": "b1",
            "silver_ids": ["s1"],
            "bronze_ids": ["b1"],
        },
    ])
    return gold.price_spread_schema.validate(df)


@pytest.fixture
def valid_opportunity_pairs_dataframe() -> pd.DataFrame:
    df = pd.DataFrame([
        {
            "product_type": "minyak goreng kemasan",
            "brand": "bimoli",
            "date": "2026-06-08",
            "cheap_city": "Sidoarjo",
            "cheap_price_per_liter": 14583.33,
            "cheap_source": "facebook",
            "expensive_city": "Surabaya",
            "expensive_price_per_liter": 17500.0,
            "expensive_source": "facebook",
            "price_diff_per_liter": 2916.67,
            "estimated_shipping_per_liter": 1500.0,
            "net_diff_per_liter": 1416.67,
            "lowest_price_silver_id": "s3",
            "lowest_price_bronze_id": "b2",
            "highest_price_silver_id": "s1",
            "highest_price_bronze_id": "b1",
            "silver_ids": ["s1", "s3"],
            "bronze_ids": ["b1", "b2"],
        },
    ])
    return gold.opportunity_pairs_schema.validate(df)


@pytest.fixture
def valid_brand_summary_dataframe() -> pd.DataFrame:
    df = pd.DataFrame([
        {
            "product_type": "minyak goreng kemasan",
            "brand": "bimoli",
            "date": "2026-06-08",
            "min_price_per_liter": 14583.33,
            "max_price_per_liter": 17500.0,
            "avg_price_per_liter": 16041.67,
            "city_count": 2,
            "listing_count": 2,
            "lowest_price_silver_id": "s3",
            "lowest_price_bronze_id": "b2",
            "highest_price_silver_id": "s1",
            "highest_price_bronze_id": "b1",
            "silver_ids": ["s1", "s3"],
            "bronze_ids": ["b1", "b2"],
        },
    ])
    return gold.brand_summary_schema.validate(df)


def test_save_and_get_price_spread_roundtrip(test_subject, valid_price_spread_dataframe, cleanup_test_files):
    filename = gold.save_price_spread(test_subject, valid_price_spread_dataframe)
    assert filename == "gold - minyak goreng test - price_spread.json"

    loaded = gold.get_price_spread(test_subject)
    assert_frame_equal(valid_price_spread_dataframe, loaded, check_dtype=False)


def test_save_and_get_opportunity_pairs_roundtrip(test_subject, valid_opportunity_pairs_dataframe, cleanup_test_files):
    filename = gold.save_opportunity_pairs(test_subject, valid_opportunity_pairs_dataframe)
    assert filename == "gold - minyak goreng test - opportunity_pairs.json"

    loaded = gold.get_opportunity_pairs(test_subject)
    assert_frame_equal(valid_opportunity_pairs_dataframe, loaded, check_dtype=False)


def test_save_and_get_brand_summary_roundtrip(test_subject, valid_brand_summary_dataframe, cleanup_test_files):
    filename = gold.save_brand_summary(test_subject, valid_brand_summary_dataframe)
    assert filename == "gold - minyak goreng test - brand_summary.json"

    loaded = gold.get_brand_summary(test_subject)
    assert_frame_equal(valid_brand_summary_dataframe, loaded, check_dtype=False)


def test_save_and_get_empty_opportunity_pairs(test_subject, cleanup_test_files):
    empty = pd.DataFrame(columns=list(gold.opportunity_pairs_schema.columns.keys()))

    gold.save_opportunity_pairs(test_subject, empty)
    loaded = gold.get_opportunity_pairs(test_subject)

    assert len(loaded) == 0
    assert set(gold.opportunity_pairs_schema.columns.keys()).issubset(loaded.columns)


def test_save_rejects_data_missing_required_column(test_subject):
    incomplete_data = pd.DataFrame([{"product_type": "minyak goreng kemasan"}])

    with pytest.raises(Exception):
        gold.save_price_spread(test_subject, incomplete_data)
