from src.storage import bronze
from parse.parser import parse_raw_text
import pandas as pd

# do scrapping
def ingest(subject: str) -> pd.DataFrame:
    print("ingest function haven't implemented")
    return pd.DataFrame({})

# Bronze layer
def store_raw(subject: str, data: pd.DataFrame):
    # bronze.save(subject, data)
    return bronze.get(subject)

# extract fields
def parse(formats: list[str], raw_text: pd.Series, lang: str) -> dict:
    return parse_raw_text(formats, raw_text, lang)
    
# standarize based on price or something
def normalize():
    print("normalize function haven't implemented")
    
# QC check
def validate():
    print("validate function haven't implemented")
    
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
def load():
    print("load function haven't implemented")
    
# gold layer
# price_spread_summary
# ├── product_type
# ├── brand
# ├── date
# ├── source
# ├── min_price_per_liter
# ├── max_price_per_liter
# ├── avg_price_per_liter
# └── city                -- nullable
def analyze():
    print("analyze function haven't implemented")

if __name__ == '__main__':
    subject = "minyak goreng"
    data = store_raw(subject, pd.DataFrame({}))
    raw_text = data["raw_text"]

    formats = ["price", "unit-quantity", "location", "brand"]
    language = "indonesia"
    parser_result = parse_raw_text(formats, raw_text, language)
    print(parser_result)

