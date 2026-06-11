import pytest
import pandas as pd
from src.storage import bronze
from src.storage.paths import data_path
from pandas.testing import assert_frame_equal


@pytest.fixture
def valid_bronze_dataframe() -> pd.DataFrame:
    return pd.DataFrame([
        {
            "id": "87de38d2-1b2a-4ae2-b37b-bd5e62ea120c",
            "source": "facebook",
            "source_id": "1234567890",
            "raw_text": "Minyak sania 10 dus 2 liter 180k, Surabaya",
            "url": "https://www.facebook.com/groups/example/posts/1234567890",
            "scraped_at": "2026-06-10T08:30:00",
            "raw_location": "Surabaya",
            "language": "id",
            "query_strategy": "keyword",
        },
        {
            "id": "21d46b9a-8702-411a-b90a-20f6e35f8150",
            "source": "tokopedia",
            "source_id": None,
            "raw_text": "Minyak Bimoli 2.5 literan karton 185rb, stok di Surabaya atau mojokerto",
            "url": "https://www.tokopedia.com/example-product",
            "scraped_at": "2026-06-10T09:15:00",
            "raw_location": None,
            "language": "id",
            "query_strategy": "kategori",
        },
    ])


@pytest.fixture
def test_subject() -> str:
    return "minyak goreng test"


@pytest.fixture
def cleanup_test_file(test_subject):
    yield
    data_path("bronze", bronze._filename(test_subject)).unlink(missing_ok=True)


def test_save_and_get_roundtrip(test_subject, valid_bronze_dataframe, cleanup_test_file):
    filename = bronze.save(test_subject, valid_bronze_dataframe)
    assert filename == "bronze - minyak goreng test.json"

    loaded = bronze.get(test_subject)
    assert_frame_equal(valid_bronze_dataframe, loaded, check_dtype=False)


def test_save_rejects_data_missing_required_column(test_subject):
    incomplete_data = pd.DataFrame([{"id": "abc-123"}])

    with pytest.raises(Exception):
        bronze.save(test_subject, incomplete_data)


def test_save_rejects_duplicate_id(test_subject, valid_bronze_dataframe):
    duplicated = pd.concat([valid_bronze_dataframe, valid_bronze_dataframe.iloc[[0]]], ignore_index=True)

    with pytest.raises(Exception):
        bronze.save(test_subject, duplicated)


def test_get_sample_minyak_goreng_data():
    data = bronze.get("minyak goreng")

    assert len(data) > 0
    assert set(bronze.bronze_schema.columns.keys()).issubset(data.columns)
