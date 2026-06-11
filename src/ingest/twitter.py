import uuid
import pandas as pd

# TODO: ganti dengan scraping asli (lihat task ingest scrapers).
# Untuk sekarang return dummy data yang merepresentasikan struktur & gaya bahasa
# tweet yang menyebut barang dagangan, biar tahap parse/normalize/dst bisa
# di-test pakai data yang mirip aslinya.
def ingest(subject: str) -> pd.DataFrame:
    return pd.DataFrame([
        {
            "id": str(uuid.uuid4()),
            "source": "twitter",
            "source_id": "1798765432109876543",
            "raw_text": "Stok minyak goreng Filma 2 liter masih ada nih gengs, 36rb aja per botol. Lokasi Semarang. #minyakgoreng #sembako",
            "url": "https://x.com/contoh_akun/status/1798765432109876543",
            "scraped_at": "2026-06-08T20:10:00",
            "raw_location": None,
            "language": "id",
            "query_strategy": "hashtag",
        },
        {
            "id": str(uuid.uuid4()),
            "source": "twitter",
            "source_id": "1798765432109877110",
            "raw_text": "Open PO minyak goreng curah jeriken 18 liter, harga 310rb. Area Jogja & sekitarnya. DM yuk! #minyakgorengmurah",
            "url": "https://x.com/contoh_akun2/status/1798765432109877110",
            "scraped_at": "2026-06-09T21:55:00",
            "raw_location": None,
            "language": "id",
            "query_strategy": "hashtag",
        },
        {
            "id": str(uuid.uuid4()),
            "source": "twitter",
            "source_id": "1798765432109877689",
            "raw_text": "Update harga: Sania 1 liter = 19rb, Bimoli 1 liter = 18.5rb, Fortune 1 liter = 17.5rb. Stok terbatas area Mojokerto #hargaminyak",
            "url": "https://x.com/contoh_akun3/status/1798765432109877689",
            "scraped_at": "2026-06-10T22:40:00",
            "raw_location": None,
            "language": "id",
            "query_strategy": "hashtag",
        },
    ])
