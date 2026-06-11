1. Ingest (paling kosong, paling banyak gap)
- Cara akses tiap source belum disebut: API resmi, scraping HTML (requests+bs4), atau browser automation (Playwright/Selenium)? Ini penting karena Facebook & marketplace platform punya anti-bot ketat, dan Twitter/X API sekarang berbayar.
Answer: Lu coba cari tau gimana cara akses apinya, sementara lu cari tau yang gratis dulu aja. kalau mereka emangg ga menyediakan api seperti facebook, bisa pakai selenium. Tapi kalau emang ada apinya, better pakai itu. Untuk twitter, coba cari tau cara gratisnya dulu aja. Sementara ini semuanya jangan ada yang berbayar. Coba lu bikin dua tipe, versi free dan paid sama seperti ada di parse yang bisa pilih bahasa.

- Query strategy: "subject" (misal "minyak goreng") itu jadi search keyword di tiap platform — tapi format pencarian tiap platform beda (hashtag di Twitter, kategori di Tokopedia/Shopee, grup di Facebook). Perlu mapping per source?
Answer: hajar semua aja, keyword, kategori, dll. Berarti kayanya harus nambah
# └── query_strategy      -- bisa "keyword", "hastag" kalau sourcenya dari twitter, "kategori" kalau dari tokopedia, dll
di bagian bronze layernya ya!

- Auth/credential & rate limit/jadwal scraping belum disinggung sama sekali.
Answer: Untuk sementara ini, memastikan codenya jalan dulu. Ini memang sengaja gue ga setting dulu, masih make sure dulu. Untuk Auth/credential & rate limit sementara karena kita nyari yang gratisan, jadi sementara ga pakai itu dulu ya. Sebisa mungkin lu cari caranya aja

- source_id: spec bilang "kalau ada" — tapi di bronze_schema cuma kolom id yang divalidasi, sisanya (termasuk source_id, source, raw_text, dll) di-comment out. Mau dibikin required per source atau tetap nullable semua?
Answer: itu gue komen kemaren karena gue lagi testing doang. Samain kaya perintah awal aja, ketika emang dia ga required gausah, yang required tetep required

- language: disebut di spec ingest (baris 26) tapi (a) belum ada di bronze_schema, (b) deteksi bahasanya pakai apa (langdetect/fasttext/manual rule), dan dilakukan per-post atau per-source?
Answer: tambahin aja di bronze_schema, jadinya
# └── language            -- bahasa yang dipakai di raw_text
deteksi bahasa pakai rekomendasi lu aja, sementara gue ga mengerti, paling tepat dan efisien untuk kasus gue aja. Lakukan per post aja

2. Bug kecil yang perlu konfirmasi
- main.py → store_raw() manggil bronze.get(subject) padahal bronze.save(...) di-comment. Apakah ini emang sengaja (testing sementara) atau kelewatan?
Answer: Itu emang sengaja testing sementara, gue gapunya patokan ngerjainnya bakal gimana pada dasarnya. Jadi gue pasrahin ke lu aja, yang penting readable, buat nanti kalau misal ada bug gue masih bisa baca

- bronze_schema cuma validasi field id, field lain semua commented — apakah mau dikunci dulu sesuai dokumentasi sebelum ingest mulai diisi, biar gak ada data "liar" masuk bronze?
Answer: itu kemaren gue testing doang, lakuin yang seharusnya aja

3. Parse
- Currency: disebut di spec (baris 37) tapi formats list di main.py (["price","unit-quantity","location","brand"]) gak include "currency", dan IndonesiaParser belum punya _extract_currency.
Answer: Nah, tambahin bang, minta tolong yak wkwk

- Normalisasi angka: _extract_price masih ngembaliin string mentah ("185rb", "180k", "185.000"), belum dikonversi ke number. Konversi string→angka itu tanggung jawab parse atau normalize?
Answer: kasih tanggung jawabnya ke parser aja

- Multi-item per post: satu raw_text bisa punya >1 brand/unit/price (misal "Bimoli 12L 250rb, Sania 18L 350rb" dalam satu postingan). Hasil parse sekarang per-field jadi list terpisah tanpa pairing — apakah satu raw_text harus pecah jadi banyak baris silver, dan gimana cara pairing brand↔price↔unit yang bener?
Answer: pecah ke banyak silver aja. Berarti perlu bronze_id nya, tambahin bronze_id nya ya biar kita tau beberapa data itu dari satu postingan yang sama yang mana. Jadinya di silver juga punya id, punya foreign key juga dari bronze_id, one to many jadinya ya

- bronze_id & parse_confidence: disebut di skema silver (comment di main.py), tapi parser belum ngembaliin id/bronze_id, dan belum ada logic buat hitung parse_confidence.
Answer: Coba tambahin aja sementara ini, gue juga baru ngeh ada parse_confidence. Soalnya gue juga belum tau parameter confidencenya dari mana. Gue bingung juga apakah ini murni kita yang kasih flaging atau dari sistem, sementara kalau dari sistem gue bingung parameternya apa. Untuk kasus ini, gue coba pasrahin ke lu aja ok

4. Normalize
- Tabel konversi "1 jeriken 18L = 18L", "1 karton 12x2L = 24L" itu sumbernya darimana? Itu kan spesifik per packaging/brand — perlu lookup table manual per brand/subject? Gimana kalau raw_text cuma bilang "10 dus" tanpa info isi per dus?
Answer: untuk case ini, kayanya di masukin ke flag aja, tapi tetap potensial. Karena nanti kita juga recheck lagi buat validasi. Sementara begini, gue belum ada pikiran buat ini

- Bentuk parameter unit_convert belum jelas — config per subject (file/dict)?
Answer: iya config per subject aja, coba lu atur dulu.

- Logic normalize ini jelas subject-specific (minyak → liter). Gimana arsitekturnya biar bisa nambah subject baru tanpa nulis ulang semua?
Answer: sementara ini untuk satu object saja, nanti kita bikin multi object based on config dari depan. Sekarang yang penting jalan dulu untuk satu object, terus kita adjust. Kalau lu mau bikin sekalian menyediakan confignya, gapapap, gas aja bwang.

5. Validate
- Threshold "harga di bawah 10rb atau di atas 50rb → flag" itu konteksnya per liter minyak goreng — apakah ini hardcoded utk minyak goreng aja, atau harus jadi config per subject (karena range harga wajar tiap barang beda jauh)?
Answer: tentu ini masuk config bro, karena beda subject beda config atau range harganya juga. Bikin confignya aja ok

- Bentuk output "flag" gimana — boolean kolom tunggal, atau list of reason strings (["price_out_of_range","unit_unrecognized"])?
Answer: kasih dua duanya aja ok. Ada flag boolean terus reasonnya apa. Setelah gue pikir pikir gue perlu data alasannya juga

6. Load & Analyze
- Skema silver/gold di main.py masih draft comment — apakah itu dipakai sebagai baseline, atau mau direvisi dulu?
Answer: sementara sebagai baseline aja. Soalnya gue masih belum nampak objectives nya

- "Antri verifikasi manual" — disimpan di mana (file terpisah silver - {subject} - pending.json?) dan workflow review-nya gimana?
Answer: sementara ini, gue mikir disimpan di bagian yang sama dengan code nya yaitu "load" dan untuk formatnya gue belum tau lagi. Gue baru sadar. Untuk ini tolong urus dulu ya, gue terima rekomendasi lu, sementara untuk case ini lu coba cover ya.

- Dedup: listing yang sama muncul lagi di scrape berikutnya (post lama masih nongol), gimana cara load/analyze nge-handle biar gak dihitung dobel?
Answer: ini kayanya perlu ada parameter range date diawal. Menurut lu gimana? Misalpun ada deduplikasi, gue mau nambah satu function berarti bernama decuplication(). Ini gue masih gatau antara setelah load() atau sebelum load(). Yang gue pikirin adalah, fungsi ini akan jalan dulu nanti secara background dan terpisah, artinya ada flagging "ready" ketika deduplikasi sudah gaada. Sementara kasarannya begini aja

- Analyze sekarang cuma hitung spread (min/max/avg per liter). Mengingat nama project "arbitrage" — apakah gold layer juga perlu nge-highlight opportunity pairs spesifik (misal harga termurah kota A vs termahal kota B, minus estimasi ongkir), atau cukup statistik spread dulu?
Answer: good, jalankan rekomendasimu oppotunity paris spesifik itu serta ada pengelompokan berdasarkan brand

7. Cross-cutting
- Multi-subject: brand list (bimoli|sania|tropical|...), lokasi list (surabaya|sidoarjo|...), dan unit list di IndonesiaParser sekarang hardcoded buat minyak goreng + kota Jawa Timur. Kalau mau scale ke barang lain (beras, gula, semen, dll), gimana generalize-nya — config per subject?
Answer: bener, config per subject aja karena tiap subject confignya bakalan beda beda 

- Orchestration: main.py sekarang cuma harness testing manual. Bentuk akhirnya gimana — CLI dengan argumen --subject, scheduler/cron buat "otomasi" yang disebut di proses #2?
Answer: Bentuk akhirnya gue pingin scheduler. Karena disini gue mau bangun data warehouse beserta pipeline nya, itu tujuan akhirnya dimana gue bisa liat data data akhir dan mengambil keputusan. Tapi itu bertahap saja, untuk sekarang, kita make sure ini jalan dulu aja, next step kita adjust pelan pelan






