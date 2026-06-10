import pandera.pandas as pa
import pandas as pd
from pathlib import Path

# bronze layer, raw storage
# raw_listings
# ├── id                  -- generated UUID
# ├── source              -- 'facebook' | 'tokopedia' | 'shopee' | dll
# ├── source_id           -- ID post/listing di platform asalnya (kalau ada)
# ├── raw_text            -- teks posting asli, utuh
# ├── url                 -- link ke posting (kalau ada)
# ├── scraped_at          -- timestamp kapan data diambil
# └── raw_location        -- teks lokasi mentah ("Surabaya", "Jawa Timur", dll) — nullable
bronze_schema = pa.DataFrameSchema({
    "id": pa.Column(str, required=True),
    # "source": pa.Column(str, required=True),
    # "source_id": pa.Column(str, required=False),
    # "raw_text": pa.Column(str, required=True),
    # "url": pa.Column(str, required=True),
    # "scraped_at": pa.Column(str, required=True),
    # "raw_location": pa.Column(str, required=True),
})
    
def save(subject: str, data: pd.DataFrame) -> str:
    try:
        filename = _filename(subject)
        
        _log("Memvalidasi komponen data...")
        data_validated = bronze_schema.validate(data)

        current_dir = Path(__file__).resolve().parent
        file_path = current_dir / filename
        
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
        current_dir = Path(__file__).resolve().parent
        file_path = current_dir / filename

        _log(f"Membaca file JSON dari: {file_path}")
        data = pd.read_json(file_path)
        
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
