import pandera.pandas as pa
import pandas as pd

from src.storage.paths import data_path

# trace columns yang ditambahin ke tiap tabel gold, biar tiap baris agregat bisa
# ditelusuri balik ke listing (silver) & posting (bronze) asalnya:
# ├── lowest_price_silver_id   -- silver.id dengan price_per_liter terendah di grup ini
# ├── lowest_price_bronze_id   -- bronze.id dari listing di atas
# ├── highest_price_silver_id  -- silver.id dengan price_per_liter tertinggi di grup ini
# ├── highest_price_bronze_id  -- bronze.id dari listing di atas
# ├── silver_ids               -- semua silver.id yang masuk ke agregat ini
# └── bronze_ids               -- semua bronze.id (unik) asal silver_ids di atas
_TRACE_COLUMNS = {
    "lowest_price_silver_id": pa.Column(str, required=True),
    "lowest_price_bronze_id": pa.Column(str, required=True),
    "highest_price_silver_id": pa.Column(str, required=True),
    "highest_price_bronze_id": pa.Column(str, required=True),
    "silver_ids": pa.Column(object, required=True),
    "bronze_ids": pa.Column(object, required=True),
}

# gold layer, hasil agregasi dari silver buat analisis arbitrage
# price_spread_summary
# ├── product_type        -- nullable
# ├── brand               -- nullable
# ├── city                -- nullable
# ├── date                -- tanggal listing (dari bronze.scraped_at, format YYYY-MM-DD)
# ├── source              -- 'facebook' | 'tokopedia' | dll
# ├── min_price_per_liter
# ├── max_price_per_liter
# ├── avg_price_per_liter
# ├── listing_count
# └── ... _TRACE_COLUMNS
price_spread_schema = pa.DataFrameSchema({
    "product_type": pa.Column(str, required=True, nullable=True),
    "brand": pa.Column(str, required=True, nullable=True),
    "city": pa.Column(str, required=True, nullable=True),
    "date": pa.Column(str, required=True),
    "source": pa.Column(str, required=True),
    "min_price_per_liter": pa.Column(float, required=True),
    "max_price_per_liter": pa.Column(float, required=True),
    "avg_price_per_liter": pa.Column(float, required=True),
    "listing_count": pa.Column(int, required=True),
    **_TRACE_COLUMNS,
}, coerce=True)

# opportunity_pairs: per product_type+brand+date, bandingin kota termurah vs termahal,
# dikurangi estimasi ongkir/liter (config analyze.estimated_shipping_per_liter) ->
# net_diff_per_liter (potensi margin arbitrage)
# lowest_price_*/highest_price_* di sini = listing cheap/expensive itu sendiri;
# silver_ids/bronze_ids = semua listing (lintas kota) yang dibandingkan buat pair ini
opportunity_pairs_schema = pa.DataFrameSchema({
    "product_type": pa.Column(str, required=True, nullable=True),
    "brand": pa.Column(str, required=True, nullable=True),
    "date": pa.Column(str, required=True),
    "cheap_city": pa.Column(str, required=True, nullable=True),
    "cheap_price_per_liter": pa.Column(float, required=True),
    "cheap_source": pa.Column(str, required=True),
    "expensive_city": pa.Column(str, required=True, nullable=True),
    "expensive_price_per_liter": pa.Column(float, required=True),
    "expensive_source": pa.Column(str, required=True),
    "price_diff_per_liter": pa.Column(float, required=True),
    "estimated_shipping_per_liter": pa.Column(float, required=True),
    "net_diff_per_liter": pa.Column(float, required=True),
    **_TRACE_COLUMNS,
}, coerce=True)

# brand_summary: rekap per brand lintas kota, buat liat brand mana yang spread-nya gede
brand_summary_schema = pa.DataFrameSchema({
    "product_type": pa.Column(str, required=True, nullable=True),
    "brand": pa.Column(str, required=True, nullable=True),
    "date": pa.Column(str, required=True),
    "min_price_per_liter": pa.Column(float, required=True),
    "max_price_per_liter": pa.Column(float, required=True),
    "avg_price_per_liter": pa.Column(float, required=True),
    "city_count": pa.Column(int, required=True),
    "listing_count": pa.Column(int, required=True),
    **_TRACE_COLUMNS,
}, coerce=True)


def save_price_spread(subject: str, data: pd.DataFrame) -> str:
    return _save(_price_spread_filename(subject), price_spread_schema, data)


def get_price_spread(subject: str) -> pd.DataFrame:
    return _get(_price_spread_filename(subject), price_spread_schema)


def save_opportunity_pairs(subject: str, data: pd.DataFrame) -> str:
    return _save(_opportunity_pairs_filename(subject), opportunity_pairs_schema, data)


def get_opportunity_pairs(subject: str) -> pd.DataFrame:
    return _get(_opportunity_pairs_filename(subject), opportunity_pairs_schema)


def save_brand_summary(subject: str, data: pd.DataFrame) -> str:
    return _save(_brand_summary_filename(subject), brand_summary_schema, data)


def get_brand_summary(subject: str) -> pd.DataFrame:
    return _get(_brand_summary_filename(subject), brand_summary_schema)


def _save(filename: str, schema: pa.DataFrameSchema, data: pd.DataFrame) -> str:
    try:
        _log(f"Memvalidasi komponen data {filename}...")
        data_validated = schema.validate(data)

        file_path = data_path("gold", filename)

        _log(f"Menyimpan data JSON {file_path} ...")
        data_validated.to_json(file_path, orient="records", indent=4)
        _log("Data berhasil disimpan (OK)!")

        return filename
    except Exception as e:
        print(f"failed to save gold file {filename}: {e}")
        raise e


def _get(filename: str, schema: pa.DataFrameSchema) -> pd.DataFrame:
    try:
        file_path = data_path("gold", filename)

        _log(f"Membaca file JSON dari: {file_path}")
        data = pd.read_json(file_path, dtype=False)

        # file kosong ("[]") kehilangan info kolom, rekonstruksi dari schema
        if data.empty and len(data.columns) == 0:
            data = pd.DataFrame(columns=list(schema.columns.keys()))

        _log("Memvalidasi ulang komponen data dari file...")
        data_validated = schema.validate(data)
        _log("Data berhasil dimuat dan terverifikasi aman (OK)!")

        return data_validated
    except Exception as e:
        print(f"failed to get gold file {filename}: {e}")
        raise e


def _price_spread_filename(subject: str) -> str:
    if not subject:
        raise Exception("subject can not be empty")

    return "gold - " + subject + " - price_spread.json"


def _opportunity_pairs_filename(subject: str) -> str:
    if not subject:
        raise Exception("subject can not be empty")

    return "gold - " + subject + " - opportunity_pairs.json"


def _brand_summary_filename(subject: str) -> str:
    if not subject:
        raise Exception("subject can not be empty")

    return "gold - " + subject + " - brand_summary.json"


def _log(message: str):
    print("[Gold] " + message + "\n")
