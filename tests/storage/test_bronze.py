import pytest
import pandas as pd
import uuid
from src.storage import bronze
from pandas.testing import assert_frame_equal

# Fixture ini bakal bikinin DataFrame tiruan sebelum test jalan
@pytest.fixture
def dummy_dataframe_save() -> pd.DataFrame:
    data = [
        {
            "id": str(uuid.uuid4()),
            "source": "facebook",
        },
        {
            "id": str(uuid.uuid4()),
        }
    ]
    return pd.DataFrame(data)

@pytest.fixture
def dummy_dataframe_get() -> pd.DataFrame:
    data = [
        {
            "id":"87de38d2-1b2a-4ae2-b37b-bd5e62ea120c",
            "source":"facebook",
        },
        {
            "id":"21d46b9a-8702-411a-b90a-20f6e35f8150",
        }
    ]
    return pd.DataFrame(data)

@pytest.fixture
def dummy_filename() -> str:
    return "minyak goreng"

def test_invalid_data_on_saving(dummy_filename, dummy_dataframe_save):
    filename = bronze.save(dummy_filename, dummy_dataframe_save)
    assert filename == "bronze - minyak goreng.json"

def test_get_data(dummy_filename, dummy_dataframe_get):
    data = bronze.get(dummy_filename)
    assert_frame_equal(dummy_dataframe_get, data)