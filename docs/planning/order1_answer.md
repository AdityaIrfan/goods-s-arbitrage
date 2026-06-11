  Hal yang lu pasrahin ke gue — ini rekomendasi gue

  1. Language detection → pakai langdetect (ringan, offline, gratis). Jalan per-row di kolom raw_text saat ingest, hasilnya masuk kolom language baru.

  2. parse_confidence → bikin scoring berbasis kelengkapan & ambiguitas hasil ekstraksi:
  - high: price, unit-quantity, brand semua ketemu tepat 1 match, gak ambigu
  - medium: ada field nullable yang kosong (misal location), atau ada ambiguity ringan tapi masih bisa di-resolve heuristik
  - low: price atau unit-quantity gak ketemu sama sekali, atau brand/unit gak dikenali, atau banyak kandidat ambigu

  3. Manual verification queue (load) → simpen di folder storage juga, file terpisah silver - {subject} - pending.json, schema sama kayak silver + tambahan review_status (pending/approved/rejected) dan flag_reasons. Row low/flagged masuk sini, high/medium langsung ke silver - {subject}.json.

  4. Dedup → setuju sama arah lu (function deduplicate() terpisah). Konkretnya:
  - Dedup exact pakai source + source_id (kalau ada)
  - Dedup near-duplicate pakai fuzzy match raw_text (rapidfuzz, threshold tinggi)
  - Param date_range (start/end) buat batasi window yang dicek
  - Tambah flag dedup_status (pending/ready) + is_duplicate/duplicate_of di row. load() cuma proses row dedup_status == "ready" and not is_duplicate
  - Posisinya: jalan setelah parse+normalize+validate, sebelum load() baca data
  
  5. Normalize unit gap (misal "10 dus" tanpa info isi per dus) → setuju, ini jadi flag (unit_conversion_incomplete) dengan confidence di-downgrade, bukan reject — nanti direcheck di validate.

  Yang berubah di skema/arsitektur (semua udah disepakati)

  - Bronze: lock schema sesuai dokumentasi awal + tambah query_strategy dan language
  - Silver: tambah id + bronze_id (one-to-many dari satu bronze row → banyak silver row)
  - Config per subject (brand list, lokasi, unit conversion, price threshold, query strategy per source) — bakal gue taruh di folder config baru, misal config/subjects/minyak_goreng.json

  Rencana eksekusi

  Karena udah ada sample data bronze (bronze - minyak goreng.json), gue saranin kita bangun dari tengah keluar — bereskan parse → normalize → validate → load → analyze pakai sample data dulu (paling cepet "jalan", sesuai prioritas lu), baru terakhir ingest (paling kompleks, butuh riset API per platform yang lu minta).

