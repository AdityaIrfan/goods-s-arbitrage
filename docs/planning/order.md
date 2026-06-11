File ini berada di folder agent, artinya untuk melihat root project kamu harus keluar satu directory "..".

Disini gue bikin program good's arbitrage, dimana gue collect data dari semua sources terkait harga barang tersebut. Scrapping data diambil dari
- Facebook post
- Facebook marketplace
- Indotrading
- Tokopedia grosir
- Shopee grosir
- Twitter atau X

Akan ada beberapa proses dari yang awal scrapping sampai pada analisis buat kita memutuskan barang mana yang akan kita kerjain. Gue akan coba terapin "Medallion Architecture" dimana akan ada 
1. "Bronze" layer yang bertugas menyimpan raw data
2. "Silver" layer yang bertugas menyimpan data dari "Bronze" layer dan setelah melalui cleaning data
3. "Gold" layer dimana analytics-ready yang diproses dari data silver

Proses proses yang akan gue buat yaitu (bisa lu liat di src/main.py):
1. ingest (src/ingest)
    Yang melakukan scrapping dari semua sources yang udah gue sebutin diatas. Kemudian akan diubah menjadi format ke bronze layer
    # ├── id                  -- generated UUID
    # ├── source              -- 'facebook' | 'tokopedia' | 'shopee' | dll
    # ├── source_id           -- ID post/listing di platform asalnya (kalau ada)
    # ├── raw_text            -- teks posting asli, utuh
    # ├── url                 -- link ke posting (kalau ada)
    # ├── scraped_at          -- timestamp kapan data diambil
    # └── raw_location        -- teks lokasi mentah ("Surabaya", "Jawa Timur", dll) — nullable
    # └── language            -- bahasa yang dipakai di raw_text
    # └── query_strategy      -- bisa "keyword", "hastag" kalau sourcenya dari twitter, "kategori" kalau dari tokopedia, dll
    Data yang akan diformat tentunya array of object ya, dalam hal ini gue coba pakai Dataframe dari pandas.

2. store raw (src/storage)
    Proses ini menyimpan data dari proses ingest ke dalam storege menjadi sebuah file json dengan format "bronze - {subject}.json". Kita ambil contoh misal minyak goreng sebagai subject, data yang disimpan akan menjadi "bronze - minyak goreng.json". Di dalamnya akan menyimpan array of object, jadi akan menyimpan banyak data terkait "minyak goreng".
    
    Code yang udah gue buat ada di bagian /src/storage/bronze.py. Disitu ada save dan get function. Karena kedepannya gue akan bangun sebuah otomasi, dimana save data dan get akan menjadi proses yang berbeda. Untuk saat ini, kita pake cuman bagian save aja. Karena kita mau testing dan make sure ini jalan dulu sebelum kita automasi.

3. parse (src/parse)
    Bertugas untuk mengesktraksi fields dari list of raw texts. Format yang akan gue gunakan seperti dibawah ini
    # ├── price             -- harga dari barang tersebut
    # ├── currency          -- currency apa yang dipakai, bisa rupiah, RP, IDR, atau mata uang yang lain
    # ├── brand             -- brand dari subject yang kita pakai, misal minyak goreng berarti brandnya bisa bimoli, sanco, dll
    # ├── location          -- lokasi dari postingan tersebut, biasanya penjual menyertakan lokasi mereka berjualan bersama di postingan
    # ├── unit-quantity     -- satuan dan kuantitasnya, misal 10 dus karton, 5 liter. Dan ini akan jadi array of unit dan quantity. Jadinya [{"dus": 10}, {"liter": 5}]. Quantity jumlahnya bisa float karena beberapa barang ada yang "2,5" atau "2.5". Satu postingan bisa juga ada lebih dari satu unit dan quantity, misalnya "10 dus karton 5 literan" maka berarti ada {"dus": 10} dan {"liter": 5}
    Untuk saat ini, gue baru menyediakan bahasa Indonesia, karena target gue adalah indonesia. Artinya ada deteksi bahasa. Gue menyediakan ini buat nanti kalau gue jualan barang luar negeri

4. normalize (src/normalize)
    Tugasnya adalah untuk menormalisai data. Kita ambil contoh untuk kasus minyak. Jadinya
    - Semua harga -> rupiah per liter
    - Semua satuan / unit -> dikonversi ke liter (1 jeriken 18L = 18L, 1 karton 12x2L = 24L)
    - Brand name -> cannonical form (bimoli, sania bukan BIMOLI, Sania) artinya to lower
    Ini akan menjadi masukan juga seperti "subject", jadi nanti ada parameter lain selain "subject" yaitu "unit_convert" mungkin ya.

5. validate (src/validate)
    Tugasnya untuk mevalidasi flag data yang mencurigakan sebelum masuk silver layer
    - Harga 10 ribu dibawah atau diatas 50 ribu -> flag
    - Satuan tidak dikenali -> flag
    - Lokasi tidak bisa di resolve -> nullable, bukan reject

6. load (src/load)
    Load ke Silver Row yang confidence-nya high dan medium masuk otomatis. Yang low atau flagged → antri untuk verifikasi manual kamu. Simpan saja sebagai "silver - {subject}.json". Gue masih belum jelas form yang bakal dipakai, jadi mungkin sementara berdasarkan rekomendasimu dulu, nanti kita adjust pelan pelan
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

7. analyze (src/analyze)
    Aggregate ke Gold Dari silver, hitung spread: min, max, avg harga per liter — bisa di-slice per brand, per kota, per source, per tanggal. Simpan saja sebagai "gold - {subject}.json". Gue masih belum jelas form yang bakal dipakai, jadi mungkin sementara berdasarkan rekomendasimu dulu, nanti kita adjust pelan pelan
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

Gue juga sediain unit test (tests) untuk memastikan perubahan yang terjadi pada kode kita tidak berdampak pada kode yang sebelumnya. Lu bikinin juga ya objectivesnya, semuanya.