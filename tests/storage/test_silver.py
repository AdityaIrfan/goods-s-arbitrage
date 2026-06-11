import pytest
import pandas as pd
from src.storage import silver
from src.storage.paths import data_path
from pandas.testing import assert_frame_equal


@pytest.fixture
def valid_silver_dataframe() -> pd.DataFrame:
    df = pd.DataFrame([
        {
            "id": "f1a2b3c4-0000-0000-0000-000000000001",
            "bronze_id": "87de38d2-1b2a-4ae2-b37b-bd5e62ea120c",
            "brand": "bimoli",
            "product_type": "minyak goreng kemasan",
            "price_raw": 35000.0,
            "price_per_liter": 17500.0,
            "unit_original": "liter",
            "quantity_per_unit": 2.0,
            "min_order": None,
            "city": "Surabaya",
            "province": None,
            "delivery_coverage": None,
            "parsed_at": "2026-06-10T08:30:00+00:00",
            "parse_confidence": "high",
        },
    ])
    # validate dulu biar dtype (mis. min_order None -> NaN) sama persis
    # dengan hasil roundtrip lewat silver.save()/get()
    return silver.silver_schema.validate(df)


@pytest.fixture
def valid_pending_dataframe(valid_silver_dataframe) -> pd.DataFrame:
    pending = valid_silver_dataframe.copy()
    pending["review_status"] = "pending"
    pending["flag_reasons"] = [["price_per_liter_out_of_range"]]
    return silver.pending_schema.validate(pending)


@pytest.fixture
def test_subject() -> str:
    return "minyak goreng test"


@pytest.fixture
def cleanup_test_files(test_subject):
    yield
    data_path("silver", silver._filename(test_subject)).unlink(missing_ok=True)
    data_path("silver", silver._pending_filename(test_subject)).unlink(missing_ok=True)


def test_save_and_get_roundtrip(test_subject, valid_silver_dataframe, cleanup_test_files):
    filename = silver.save(test_subject, valid_silver_dataframe)
    assert filename == "silver - minyak goreng test.json"

    loaded = silver.get(test_subject)
    assert_frame_equal(valid_silver_dataframe, loaded, check_dtype=False)


def test_save_and_get_pending_roundtrip(test_subject, valid_pending_dataframe, cleanup_test_files):
    filename = silver.save_pending(test_subject, valid_pending_dataframe)
    assert filename == "silver - minyak goreng test - pending.json"

    loaded = silver.get_pending(test_subject)
    assert_frame_equal(valid_pending_dataframe, loaded, check_dtype=False)


def test_save_and_get_empty_pending(test_subject, cleanup_test_files):
    empty = pd.DataFrame(columns=list(silver.pending_schema.columns.keys()))

    silver.save_pending(test_subject, empty)
    loaded = silver.get_pending(test_subject)

    assert len(loaded) == 0
    assert set(silver.pending_schema.columns.keys()).issubset(loaded.columns)


def test_save_rejects_data_missing_required_column(test_subject):
    incomplete_data = pd.DataFrame([{"id": "abc-123"}])

    with pytest.raises(Exception):
        silver.save(test_subject, incomplete_data)


def test_save_rejects_duplicate_id(test_subject, valid_silver_dataframe):
    duplicated = pd.concat([valid_silver_dataframe, valid_silver_dataframe.iloc[[0]]], ignore_index=True)

    with pytest.raises(Exception):
        silver.save(test_subject, duplicated)
