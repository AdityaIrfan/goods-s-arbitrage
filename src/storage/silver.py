import pandera.pandas as pa
import pandas as pd

from src.storage.paths import data_path

# silver layer, hasil parse + normalize + validate yang siap dianalisis
# parsed_listings
# ├── id                  -- id listing (1 bronze row bisa pecah jadi banyak silver row)
# ├── bronze_id           -- foreign key ke raw_listings (bronze)
# ├── brand               -- 'bimoli' | 'sania' | 'curah' | null, sudah canonical (lowercase)
# ├── product_type        -- '{subject} kemasan' | '{subject} curah' | null
# ├── price_raw           -- harga asli dari postingan — nullable
# ├── price_per_liter     -- hasil konversi ke rupiah/liter — nullable
# ├── unit_original       -- satuan utama yang disebut di postingan ('karton', 'jeriken', 'liter', dll) — nullable
# ├── quantity_per_unit   -- isi 1 unit_original dalam liter — nullable
# ├── min_order           -- minimum order quantity — nullable
# ├── city                -- nullable
# ├── province            -- nullable
# ├── delivery_coverage   -- nullable, teks bebas ("Jawa-Bali", dll)
# ├── parsed_at           -- timestamp ISO 8601
# └── parse_confidence    -- 'high' | 'medium' | 'low'
silver_schema = pa.DataFrameSchema({
    "id": pa.Column(str, required=True, unique=True),
    "bronze_id": pa.Column(str, required=True),
    "brand": pa.Column(str, required=True, nullable=True),
    "product_type": pa.Column(str, required=True, nullable=True),
    "price_raw": pa.Column(float, required=True, nullable=True),
    "price_per_liter": pa.Column(float, required=True, nullable=True),
    "unit_original": pa.Column(str, required=True, nullable=True),
    "quantity_per_unit": pa.Column(float, required=True, nullable=True),
    "min_order": pa.Column(float, required=True, nullable=True),
    "city": pa.Column(str, required=True, nullable=True),
    "province": pa.Column(str, required=True, nullable=True),
    "delivery_coverage": pa.Column(str, required=True, nullable=True),
    "parsed_at": pa.Column(str, required=True),
    "parse_confidence": pa.Column(str, required=True),
}, coerce=True)

# antrian verifikasi manual: skema sama seperti silver_schema, ditambah
# review_status (pending/approved/rejected) dan flag_reasons dari tahap validate
pending_schema = silver_schema.add_columns({
    "review_status": pa.Column(str, required=True),
    "flag_reasons": pa.Column(object, required=True),
})


def save(subject: str, data: pd.DataFrame) -> str:
    return _save(_filename(subject), silver_schema, data)


def get(subject: str) -> pd.DataFrame:
    return _get(_filename(subject), silver_schema)


def save_pending(subject: str, data: pd.DataFrame) -> str:
    return _save(_pending_filename(subject), pending_schema, data)


def get_pending(subject: str) -> pd.DataFrame:
    return _get(_pending_filename(subject), pending_schema)


def _save(filename: str, schema: pa.DataFrameSchema, data: pd.DataFrame) -> str:
    try:
        _log(f"Memvalidasi komponen data {filename}...")
        data_validated = schema.validate(data)

        file_path = data_path("silver", filename)

        _log(f"Menyimpan data JSON {file_path} ...")
        data_validated.to_json(file_path, orient="records", indent=4)
        _log("Data berhasil disimpan (OK)!")

        return filename
    except Exception as e:
        print(f"failed to save silver file {filename}: {e}")
        raise e


def _get(filename: str, schema: pa.DataFrameSchema) -> pd.DataFrame:
    try:
        file_path = data_path("silver", filename)

        _log(f"Membaca file JSON dari: {file_path}")
        # dtype=False biar pandas ga sok pintar nebak tipe data
        data = pd.read_json(file_path, dtype=False)

        # file kosong ("[]") kehilangan info kolom, rekonstruksi dari schema
        if data.empty and len(data.columns) == 0:
            data = pd.DataFrame(columns=list(schema.columns.keys()))

        _log("Memvalidasi ulang komponen data dari file...")
        data_validated = schema.validate(data)
        _log("Data berhasil dimuat dan terverifikasi aman (OK)!")

        return data_validated
    except Exception as e:
        print(f"failed to get silver file {filename}: {e}")
        raise e


def _filename(subject: str) -> str:
    if not subject:
        raise Exception("subject can not be empty")

    return "silver - " + subject + ".json"


def _pending_filename(subject: str) -> str:
    if not subject:
        raise Exception("subject can not be empty")

    return "silver - " + subject + " - pending.json"


def _log(message: str):
    print("[Silver] " + message + "\n")
