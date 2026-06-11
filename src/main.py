from src.storage import bronze, silver
from src.parse.parser import parse_raw_text
from src.normalize.normalize import normalize_listings
from src.validate.validate import validate_listings
from src.load.dedup import deduplicate as deduplicate_bronze
from src.load.load import load_listings
from src.analyze.analyze import analyze_listings
from src.ingest import SOURCES
import pandas as pd

# do scrapping
# NOTE: tiap source di SOURCES masih return dummy data (lihat src/ingest/*.py),
# belum scraping asli. Tujuannya biar pipeline lain bisa di-test dulu pakai
# data yang formatnya udah sesuai bronze_schema.
def ingest(subject: str) -> pd.DataFrame:
    raw_data = [fetch(subject) for fetch in SOURCES.values()]
    return pd.concat(raw_data, ignore_index=True)

# Bronze layer: simpan hasil ingest
def store_raw(subject: str, data: pd.DataFrame) -> str:
    return bronze.save(subject, data)

# extract fields
def parse(formats: list[str], data: pd.DataFrame, lang: str, subject: str) -> list[dict]:
    return parse_raw_text(formats, data, lang, subject)
    
# standarize based on price or something
def normalize(parsed: list[dict], subject: str) -> list[dict]:
    return normalize_listings(parsed, subject)
    
# QC check
def validate(normalized: list[dict], subject: str) -> list[dict]:
    return validate_listings(normalized, subject)
    
# tandai baris bronze yang duplikat (exact via source+source_id, near-duplicate via raw_text)
# sebelum load() membaca data, biar listing yang sama gak kehitung dobel
def deduplicate(bronze_data: pd.DataFrame, date_range: tuple[str, str] | None = None) -> pd.DataFrame:
    return deduplicate_bronze(bronze_data, date_range)

# silver layer
# parsed_listings
# ├── id
# ├── bronze_id           -- foreign key ke raw_listings
# ├── brand               -- 'Bimoli' | 'Sania' | 'curah' | null
# ├── product_type        -- 'minyak goreng kemasan' | 'minyak goreng curah'
# ├── price_raw           -- angka harga yang diambil
# ├── price_per_liter     -- hasil konversi ke satuan standar
# ├── unit_original       -- satuan asli: 'karton', 'jeriken', 'liter', dll
# ├── quantity_per_unit   -- isi per karton/jeriken (misal: 12, 20, dll)
# ├── min_order           -- minimum order quantity — nullable
# ├── city                -- nullable
# ├── province            -- nullable
# ├── delivery_coverage   -- nullable, teks bebas ("Jawa-Bali", dll)
# ├── parsed_at           -- timestamp
# └── parse_confidence    -- 'high' | 'medium' | 'low' (seberapa yakin hasil parsing-nya)
# row dengan parse_confidence high/medium dan tidak flagged -> "silver - {subject}.json"
# row low/flagged -> antri verifikasi manual di "silver - {subject} - pending.json"
def load(validated: list[dict], subject: str, dedup_data: pd.DataFrame | None = None) -> dict:
    return load_listings(validated, subject, dedup_data)
    
# gold layer
# price_spread_summary
# ├── product_type        -- nullable
# ├── brand               -- nullable
# ├── city                -- nullable
# ├── date                -- dari bronze.scraped_at (YYYY-MM-DD)
# ├── source
# ├── min_price_per_liter
# ├── max_price_per_liter
# ├── avg_price_per_liter
# └── listing_count
#
# opportunity_pairs
# per product_type+brand+date, kota termurah vs termahal, dikurangi estimasi
# ongkir/liter (config analyze.estimated_shipping_per_liter) -> net_diff_per_liter
#
# brand_summary
# rekap per product_type+brand+date lintas kota (min/max/avg, city_count, listing_count)
def analyze(silver_data: pd.DataFrame, bronze_data: pd.DataFrame, subject: str) -> dict:
    return analyze_listings(silver_data, bronze_data, subject)

if __name__ == '__main__':
    subject = "minyak goreng"

    data = ingest(subject)
    store_raw(subject, data)

    # data = bronze.get(subject)

    formats = ["price", "currency", "unit-quantity", "location", "brand"]
    language = "indonesia"
    parsed = parse(formats, data, language, subject)

    normalized = normalize(parsed, subject)

    validated = validate(normalized, subject)

    dedup_data = deduplicate(data)
    result = load(validated, subject, dedup_data)
    print(result)

    silver_data = silver.get(subject)
    gold_result = analyze(silver_data, data, subject)
    print(gold_result)

