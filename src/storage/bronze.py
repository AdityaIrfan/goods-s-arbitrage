import pandera.pandas as pa
import pandas as pd

from src.storage.paths import data_path

# bronze layer, raw storage
# raw_listings
# ├── id                  -- generated UUID
# ├── source              -- 'facebook' | 'tokopedia' | 'shopee' | dll
# ├── source_id           -- ID post/listing di platform asalnya (kalau ada) — nullable
# ├── raw_text            -- teks posting asli, utuh
# ├── url                 -- link ke posting (kalau ada) — nullable
# ├── scraped_at          -- timestamp kapan data diambil (ISO 8601)
# ├── raw_location        -- teks lokasi mentah ("Surabaya", "Jawa Timur", dll) — nullable
# ├── language            -- bahasa yang dipakai di raw_text (misal "id", "en")
# └── query_strategy      -- "keyword", "hashtag" (twitter), "kategori" (tokopedia/shopee), dll
bronze_schema = pa.DataFrameSchema({
    "id": pa.Column(str, required=True, unique=True),
    "source": pa.Column(str, required=True),
    "source_id": pa.Column(str, required=True, nullable=True),
    "raw_text": pa.Column(str, required=True, checks=pa.Check.str_length(min_value=1)),
    "url": pa.Column(str, required=True, nullable=True),
    "scraped_at": pa.Column(str, required=True),
    "raw_location": pa.Column(str, required=True, nullable=True),
    "language": pa.Column(str, required=True),
    "query_strategy": pa.Column(str, required=True),
}, coerce=True)
    
def save(subject: str, data: pd.DataFrame) -> str:
    try:
        filename = _filename(subject)
        
        _log("Memvalidasi komponen data...")
        data_validated = bronze_schema.validate(data)

        file_path = data_path("bronze", filename)

        _log(f"Menyimpan data JSON {file_path} ...")
        # orient="records" biar bentuknya list of json object standar, indent biar rapi dibaca manusia
        data_validated.to_json(file_path, orient="records", indent=4)
        _log("Data berhasil disimpan (OK)!")

        return filename
    except Exception as e:
        print(f"failed to save bronze file: {e}")
        raise e

def get(subject: str) -> pd.DataFrame:
    try:
        filename = _filename(subject)
        file_path = data_path("bronze", filename)

        _log(f"Membaca file JSON dari: {file_path}")
        # dtype=False biar pandas ga sok pintar nebak tipe data (misal source_id "1234567890" jadi number)
        data = pd.read_json(file_path, dtype=False)
        
        _log("Memvalidasi ulang komponen data dari file...")
        data_validated = bronze_schema.validate(data)
        _log("Data berhasil dimuat dan terverifikasi aman (OK)!")
        
        return data_validated
    except Exception as e:
        print(f"failed to get bronze file: {e}")
        raise e
    
def _filename(subject: str) -> str:
    if not subject:
        raise Exception("subject can not be empty")
    
    return "bronze - "+ subject + ".json"

def _log(message: str):
    print("[Bronze] " + message + "\n")
