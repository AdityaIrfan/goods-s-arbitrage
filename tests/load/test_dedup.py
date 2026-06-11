import pandas as pd

from src.load.dedup import deduplicate


def _bronze_row(**overrides) -> dict:
    base = {
        "id": "row-1",
        "source": "facebook",
        "source_id": "1001",
        "raw_text": "Jual Minyak Goreng Bimoli 2L, harga 35rb. Surabaya",
        "url": "https://example.com/1",
        "scraped_at": "2026-06-08T09:00:00",
        "raw_location": None,
        "language": "id",
        "query_strategy": "keyword",
    }
    base.update(overrides)
    return base


def test_unique_rows_are_not_flagged_as_duplicate():
    data = pd.DataFrame([
        _bronze_row(id="row-1", source_id="1001", raw_text="Jual Bimoli 2L 35rb Surabaya"),
        _bronze_row(id="row-2", source_id="1002", raw_text="Jual Sania 1L 19rb Mojokerto", scraped_at="2026-06-09T09:00:00"),
    ])

    result = deduplicate(data)

    assert (result["dedup_status"] == "ready").all()
    assert (~result["is_duplicate"]).all()
    assert result["duplicate_of"].isna().all()


def test_exact_duplicate_via_source_and_source_id():
    data = pd.DataFrame([
        _bronze_row(id="row-1", source_id="1001", scraped_at="2026-06-08T09:00:00"),
        _bronze_row(id="row-2", source_id="1001", scraped_at="2026-06-09T09:00:00", raw_text="repost: Jual Minyak Goreng Bimoli 2L, harga 35rb. Surabaya"),
    ])

    result = deduplicate(data)
    by_id = result.set_index("id")

    assert by_id.loc["row-1", "is_duplicate"] == False
    assert by_id.loc["row-2", "is_duplicate"] == True
    assert by_id.loc["row-2", "duplicate_of"] == "row-1"


def test_near_duplicate_raw_text_without_source_id():
    data = pd.DataFrame([
        _bronze_row(id="row-1", source_id=None, raw_text="Jual Minyak Goreng Bimoli 2L, harga 35rb per pcs. Ready stock area Surabaya, minat order chat ya kak", scraped_at="2026-06-08T09:00:00"),
        _bronze_row(id="row-2", source_id=None, raw_text="Jual Minyak Goreng Bimoli 2L, harga 35rb per pcs. Ready stock area Surabaya, minat order chat ya kakk", scraped_at="2026-06-09T09:00:00"),
    ])

    result = deduplicate(data)
    by_id = result.set_index("id")

    assert by_id.loc["row-2", "is_duplicate"] == True
    assert by_id.loc["row-2", "duplicate_of"] == "row-1"


def test_different_raw_text_is_not_flagged():
    data = pd.DataFrame([
        _bronze_row(id="row-1", source_id=None, raw_text="Jual Minyak Goreng Bimoli 2L, harga 35rb. Surabaya", scraped_at="2026-06-08T09:00:00"),
        _bronze_row(id="row-2", source_id=None, raw_text="Stok minyak Sania 1 dus isi 12 botol, harga 175.000/dus. Sidoarjo", scraped_at="2026-06-09T09:00:00"),
    ])

    result = deduplicate(data)
    by_id = result.set_index("id")

    assert by_id.loc["row-2", "is_duplicate"] == False


def test_date_range_marks_out_of_window_rows_as_pending():
    data = pd.DataFrame([
        _bronze_row(id="row-1", source_id="1001", scraped_at="2026-06-01T09:00:00"),
        _bronze_row(id="row-2", source_id="1002", scraped_at="2026-06-10T09:00:00", raw_text="Stok minyak Sania 1 dus isi 12 botol, harga 175.000/dus. Sidoarjo"),
    ])

    result = deduplicate(data, date_range=("2026-06-08T00:00:00", "2026-06-12T00:00:00"))
    by_id = result.set_index("id")

    assert by_id.loc["row-1", "dedup_status"] == "pending"
    assert by_id.loc["row-2", "dedup_status"] == "ready"
