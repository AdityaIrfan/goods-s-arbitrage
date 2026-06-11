import pytest

from src.config.loader import load_subject_config


def test_load_subject_config_minyak_goreng():
    config = load_subject_config("minyak goreng")

    assert config["subject"] == "minyak goreng"
    assert "brands" in config["parse"]
    assert "units" in config["parse"]
    assert config["normalize"]["target_unit"] == "liter"
    assert "price_per_liter_min" in config["validate"]
    assert "price_per_liter_max" in config["validate"]


def test_load_subject_config_unknown_subject_raises():
    with pytest.raises(FileNotFoundError):
        load_subject_config("barang yang tidak ada")
