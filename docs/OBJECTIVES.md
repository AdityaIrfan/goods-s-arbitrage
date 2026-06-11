# Goods Arbitrage — Objectives

Pipeline buat collect harga barang (subject pertama: "minyak goreng") dari beberapa
sumber, dibersihin & dinormalisasi, terus dianalisis buat nemu *price arbitrage*
(beli murah di satu kota, jual/kirim ke kota yang harganya lebih mahal).

Arsitekturnya pakai **Medallion**: Bronze (raw) → Silver (cleaned & terstruktur) →
Gold (analytics-ready).

## Pipeline (src/main.py)

```
ingest → store_raw (bronze) → parse → normalize → validate
       → deduplicate → load (silver + pending review) → analyze (gold)
```

Semua stage di-orkestrasi per `subject` (string, misal `"minyak goreng"`) dan
sebagian besar parameternya datang dari config per-subject di
`src/config/subjects/{subject}.json` (lihat bagian [Config](#config)).

Status saat ini: stage 2–8 (bronze → analyze) sudah jalan end-to-end memakai
data dummy dari `src/ingest/*`. Stage 1 (ingest/scraping asli) masih
placeholder — lihat [Status & roadmap](#status--roadmap).

---

## Project layout

```
.
├── data/                  # output tiap layer, di-gitignore (regenerable via `python -m src.main`)
│   ├── bronze/
│   ├── silver/
│   └── gold/
├── docs/
│   ├── OBJECTIVES.md      # dokumen ini
│   └── planning/          # catatan diskusi/keputusan desain (order.md, dst)
├── src/
│   ├── main.py            # orkestrasi pipeline
│   ├── config/            # loader + config per-subject (src/config/subjects/*.json)
│   ├── ingest/             # scraper per source (lihat status #1)
│   ├── parse/ normalize/ validate/ load/ analyze/
│   └── storage/           # bronze.py / silver.py / gold.py + paths.py (resolve ke data/)
└── tests/                 # mirror struktur src/, satu folder per stage
```

`src/storage/paths.py::data_path(layer, filename)` adalah satu-satunya tempat
yang tau lokasi `data/{layer}/` — semua modul storage & test fixture pakai ini
biar gak ada path absolut yang di-hardcode ulang.

---

## 1. Ingest — `src/ingest/`

**Objective**: scraping `raw_text` postingan dari tiap sumber, lalu konversi ke
format `bronze_schema` (lihat di bawah).

Sumber yang ditarget: Facebook (post & marketplace), Indotrading, Tokopedia
Grosir, Shopee Grosir, Twitter/X. Tiap module nyediain `ingest(subject) ->
pd.DataFrame`, didaftarkan di `src/ingest/__init__.py::SOURCES`.

`query_strategy` per source dikonfigurasi di `config.ingest.query_strategy`
(`"keyword"`, `"hashtag"`, `"kategori"`, dll) dan ikut disimpan di kolom bronze
`query_strategy`.

**Status**: semua module masih return dummy data yang formatnya sudah sesuai
`bronze_schema`, biar stage selanjutnya bisa di-test. Implementasi scraping
asli = task #7 (lihat roadmap).

---

## 2. Bronze (storage) — `src/storage/bronze.py`

**Objective**: simpan raw data hasil ingest apa adanya, jadi `bronze -
{subject}.json`.

`raw_listings` (`bronze_schema`, `coerce=True`):

| kolom | tipe | nullable | keterangan |
|---|---|---|---|
| `id` | str | unique, required | UUID, di-generate saat ingest |
| `source` | str | required | `'facebook'` \| `'tokopedia'` \| dll |
| `source_id` | str | nullable | ID post/listing asli kalau ada |
| `raw_text` | str | required (min 1 char) | teks posting utuh |
| `url` | str | nullable | link ke posting |
| `scraped_at` | str | required | timestamp ISO 8601 |
| `raw_location` | str | nullable | lokasi mentah dari postingan |
| `language` | str | required | `"id"`, `"en"`, dll |
| `query_strategy` | str | required | `"keyword"` / `"hashtag"` / `"kategori"` |

`save(subject, df)` dan `get(subject)` — validasi schema sebelum simpan & lagi
pas baca balik.

---

## 3. Parse — `src/parse/`

**Objective**: ekstrak field terstruktur dari `raw_text`. Dispatch berdasarkan
`language` lewat `src/parse/parser.py::parse_raw_text(formats, data, lang,
subject)` — saat ini cuma `"indonesia"` (`IndonesiaParser`), tapi arsitekturnya
siap nambah parser bahasa lain.

Tiap baris bronze bisa pecah jadi **banyak item** kalau satu posting nyebut
beberapa brand sekaligus (misal "Fortune 2L 32rb, Tropical 2L 33rb") —
`_split_segments` motong `raw_text` per brand match. Tiap item dapet:

| field | keterangan |
|---|---|
| `id` | UUID baru per item (jadi `silver.id` nanti) |
| `bronze_id` | foreign key ke `bronze.id` (one-to-many) |
| `price` | angka hasil konversi (`"185rb"` / `"185.000"` / `"18.5rb"` → float) |
| `currency` | saat ini selalu `"IDR"` |
| `brand` | match pertama dari `config.parse.brands`, atau `null` |
| `location` | match pertama dari `config.parse.locations`, atau `null` |
| `unit-quantity` | dict `{satuan: qty}`, misal `{"karton": 1, "botol": 6, "liter": 1}` |
| `parse_confidence` | `"high"` \| `"medium"` \| `"low"` |

**`parse_confidence` scoring** (`_score_confidence`):
- `"low"` kalau price atau unit-quantity sama sekali gak ketemu, atau ada
  >1 kandidat price/brand (ambigu)
- `"medium"` kalau brand atau location gak ketemu (nullable, tapi nge-reduce
  keyakinan)
- `"high"` kalau semua field penting ketemu tepat & gak ambigu

---

## 4. Normalize — `src/normalize/normalize.py`

**Objective**: standarisasi unit ke liter & brand ke canonical form, hitung
`price_per_liter`.

- `brand` → lowercase
- `unit-quantity` → total liter, pakai `config.normalize.unit_conversion`
  (misal `{"liter": 1, "jeriken": 18, "kg": 1.087}`). Kalau ada packaging
  bersarang (`{"karton": 1, "botol": 6, "liter": 2}`), unit dasar (liter/kg/
  jeriken) dikali semua faktor packaging lain → `1 karton × 6 botol × 2 liter
  = 12 liter`.
- `price_per_liter = price / total_liter`
- Kalau unit gak bisa di-resolve sepenuhnya (misal "10 dus" tanpa info isi per
  dus) → `unit_conversion_incomplete = true`, `total_liter = null`,
  `price_per_liter = null`, dan `parse_confidence` di-downgrade satu tingkat
  (`high → medium → low`, gak pernah reject).

---

## 5. Validate — `src/validate/validate.py`

**Objective**: nge-flag data mencurigakan sebelum masuk silver — bukan reject,
cuma flag (`is_flagged: bool` + `flag_reasons: list[str]`).

Flag yang dicek (threshold dari `config.validate`):
- `price_missing` — `price` null
- `unit_conversion_incomplete` — diteruskan dari normalize
- `price_per_liter_out_of_range` — di luar
  `[price_per_liter_min, price_per_liter_max]`

Lokasi yang gak ke-resolve (`location: null`) **tidak** di-flag — itu
diperbolehkan nullable sampai ke silver (`city`).

---

## 6. Load — `src/load/` + `src/storage/silver.py`

### 6.1 Deduplicate — `src/load/dedup.py`

Jalan di **bronze data**, sebelum `load()`. Output: kolom tambahan
`dedup_status` (`"ready"` / `"pending"`), `is_duplicate`, `duplicate_of`.

- **Exact dedup**: `source` + `source_id` sama → baris yang lebih baru (by
  `scraped_at`) ditandai duplikat dari yang pertama
- **Near-duplicate**: kalau `source_id` null, bandingin `raw_text` pakai
  `difflib.SequenceMatcher` (ratio ≥ 0.92 = duplikat). *(rapidfuzz belum
  dipakai karena belum ada di dependencies — bisa di-swap nanti kalau mau.)*
- **`date_range`** (opsional, `(start, end)` ISO string): baris dengan
  `scraped_at` di luar window ditandai `dedup_status = "pending"` (belum
  diproses, nunggu window berikutnya)

`load()` cuma proses baris dengan `dedup_status == "ready" and not
is_duplicate`.

### 6.2 Load — `src/load/load.py` + Silver schema

**Objective**: tulis baris silver, route ke approved vs antrian manual review.

`parsed_listings` (`silver_schema`, `coerce=True`) — file `silver -
{subject}.json`:

| kolom | nullable | keterangan |
|---|---|---|
| `id` | unique, required | reuse dari `id` parse (1 bronze → banyak silver) |
| `bronze_id` | required | FK ke `bronze.id` |
| `brand` | ✓ | canonical lowercase, atau `null` |
| `product_type` | ✓ | `"{subject} kemasan"` / `"{subject} curah"` / `null` |
| `price_raw` | ✓ | harga asli dari posting |
| `price_per_liter` | ✓ | hasil normalize |
| `unit_original` | ✓ | unit "terluar" (prioritas: karton > jeriken > botol > pcs > sachet > liter > kg) |
| `quantity_per_unit` | ✓ | berapa liter per `unit_original` (`price_raw / price_per_liter`) |
| `min_order` | ✓ | belum diisi (selalu `null` untuk sekarang) |
| `city` | ✓ | dari `location` |
| `province` | ✓ | belum diisi |
| `delivery_coverage` | ✓ | belum diisi |
| `parsed_at` | required | timestamp ISO 8601 saat `load()` jalan |
| `parse_confidence` | required | `"high"` \| `"medium"` \| `"low"` |

**Routing**: `parse_confidence ∈ {high, medium}` **dan** `not is_flagged` →
`silver - {subject}.json`. Selain itu (low, atau flagged) → `silver -
{subject} - pending.json` (`pending_schema` = silver + `review_status` +
`flag_reasons`), nunggu verifikasi manual.

---

## 7. Analyze — `src/analyze/analyze.py` + `src/storage/gold.py`

**Objective**: agregasi silver (di-join ke bronze buat dapet `source` &
`date`) jadi 3 tabel gold, semuanya difilter row dengan `price_per_liter` non-null.

### Trace columns (semua tabel gold)
Tiap baris gold (hasil agregat dari ≥1 listing) ikut bawa kolom buat
nelusurin balik ke listing (silver) & posting (bronze) asalnya:

| kolom | keterangan |
|---|---|
| `lowest_price_silver_id` | `silver.id` dengan `price_per_liter` terendah di grup ini |
| `lowest_price_bronze_id` | `bronze.id` dari listing di atas |
| `highest_price_silver_id` | `silver.id` dengan `price_per_liter` tertinggi di grup ini |
| `highest_price_bronze_id` | `bronze.id` dari listing di atas |
| `silver_ids` | array semua `silver.id` yang masuk ke agregat ini |
| `bronze_ids` | array `bronze.id` unik asal `silver_ids` di atas |

Untuk `opportunity_pairs`, `lowest_price_*`/`highest_price_*` = listing
cheap/expensive itu sendiri, dan `silver_ids`/`bronze_ids` = semua listing
(lintas kota) yang dibandingkan buat pair tsb.

### `price_spread_summary` → `gold - {subject} - price_spread.json`
Group by `product_type, brand, city, date, source` (semua key boleh null,
`dropna=False`):
`min_price_per_liter`, `max_price_per_liter`, `avg_price_per_liter`,
`listing_count`, + trace columns.

### `opportunity_pairs` → `gold - {subject} - opportunity_pairs.json`
Per `product_type + brand + date`, cari kota termurah vs termahal (butuh ≥2
kota berbeda). Hitung:
- `price_diff_per_liter = expensive - cheap`
- `net_diff_per_liter = price_diff_per_liter -
  config.analyze.estimated_shipping_per_liter`

`net_diff_per_liter` positif = potensi margin arbitrage per liter setelah
estimasi ongkir.

### `brand_summary` → `gold - {subject} - brand_summary.json`
Per `product_type + brand + date`, lintas semua kota:
`min/max/avg_price_per_liter`, `city_count`, `listing_count`, + trace columns.

---

## Config

Per-subject JSON di `src/config/subjects/{subject_snake_case}.json`, dimuat
lewat `src/config/loader.py::load_subject_config(subject)`:

```jsonc
{
  "subject": "minyak goreng",
  "parse": {
    "brands": [...],       // dipakai parse (brand match + segmenting)
    "locations": [...],    // dipakai parse (location match)
    "units": {...}         // alias unit -> unit kanonik (dus -> karton, dll)
  },
  "normalize": {
    "target_unit": "liter",
    "unit_conversion": { "liter": 1, "jeriken": 18, "kg": 1.087 }
  },
  "validate": {
    "price_per_liter_min": 10000,
    "price_per_liter_max": 50000
  },
  "analyze": {
    "estimated_shipping_per_liter": 1500
  },
  "ingest": {
    "query_strategy": { "facebook": "keyword", "tokopedia_grosir": "kategori", ... }
  }
}
```

Subject `"minyak goreng test"` (`minyak_goreng_test.json`) adalah copy yang
dipakai unit test, biar test gak nulis ke file produksi `minyak goreng`.

---

## Testing

```bash
.venv/bin/python -m pytest -q
```

52 test, satu folder per stage (`tests/{config,storage,parse,normalize,
validate,load,analyze}/`), nutupin:

- **config**: `load_subject_config` (found/not found)
- **storage**: bronze/silver/gold — save/get roundtrip, schema rejection
  (kolom hilang, duplicate id), empty-file roundtrip
- **parse**: ekstraksi price/currency/brand/location/unit-quantity,
  multi-item splitting, `parse_confidence` scoring
- **normalize**: konversi unit (sederhana, nested packaging, kg, unit gak
  dikenal), confidence downgrade
- **validate**: tiap flag reason + kombinasi
- **load**: routing approved/pending, derivasi `product_type` /
  `unit_original` / `quantity_per_unit`, filter dedup
- **analyze**: agregasi price spread, opportunity pair detection (incl. kasus
  cuma 1 kota = no pair), brand summary

File yang ditulis test selalu ke namespace `"... test"` (`silver - minyak
goreng test.json`, `gold - minyak goreng test - *.json`, dll) dan dibersihin
lewat fixture `cleanup_*` setelah test selesai.

`src/ingest/` belum punya test — masih dummy data, nunggu task #7.

---

## Status & roadmap

| # | Stage | Status |
|---|---|---|
| 1 | Ingest (scraping asli) | **pending** — semua source masih dummy data |
| 2 | Bronze schema + config per subject | done |
| 3 | Parse (extraction + confidence + multi-item) | done |
| 4 | Normalize (unit → liter, canonical brand) | done |
| 5 | Validate (flagging) | done |
| 6 | Load (silver + pending queue + dedup) | done |
| 7 | Analyze (gold: spread, opportunity pairs, brand summary) | done |
| 8 | Objectives doc + unit tests | done (doc ini; tests akan nambah lagi pas ingest asli masuk) |

**Next**: implement scraper asli per source (task #7) — riset API gratis
dulu per platform, fallback browser automation (Selenium/Playwright) kalau
gak ada API gratis. Polanya mengikuti `src/parse/parser.py` (dispatch
free/paid mirip dispatch bahasa) — ditentukan nanti pas dikerjain.

Begitu ingest asli masuk, dokumen ini & test suite di-update buat
nyesuaiin: tambah test per-source ingest, dan update bagian "Status &
roadmap" + "Ingest" di atas.
