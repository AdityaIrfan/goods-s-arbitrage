import uuid
import pandas as pd

# TODO: ganti dengan scraping asli (lihat task ingest scrapers).
# Untuk sekarang return dummy data yang merepresentasikan struktur & gaya bahasa
# raw_text dari postingan Facebook (grup/halaman publik), biar tahap parse/normalize/dst
# bisa di-test pakai data yang mirip aslinya.
def ingest(subject: str) -> pd.DataFrame:
    return pd.DataFrame([
        {
            "id": str(uuid.uuid4()),
            "source": "facebook",
            "source_id": "10234567891234567",
            "raw_text": "Jual Minyak Goreng Bimoli 2L, harga 35rb per pcs. Ready stock area Surabaya, minat order chat ya kak \U0001F64F",
            "url": "https://www.facebook.com/groups/jualbelisembako/posts/10234567891234567",
            "scraped_at": "2026-06-08T09:12:00",
            "raw_location": None,
            "language": "id",
            "query_strategy": "keyword",
        },
        {
            "id": str(uuid.uuid4()),
            "source": "facebook",
            "source_id": "10234567891234911",
            "raw_text": "Stok minyak Sania 1 dus isi 12 botol @1 liter, harga 175.000/dus. Lokasi Sidoarjo, bisa COD",
            "url": "https://www.facebook.com/groups/jualbelisembako/posts/10234567891234911",
            "scraped_at": "2026-06-09T14:40:00",
            "raw_location": None,
            "language": "id",
            "query_strategy": "keyword",
        },
        {
            "id": str(uuid.uuid4()),
            "source": "facebook",
            "source_id": "10234567891235202",
            "raw_text": "Promo akhir bulan! Minyak goreng Fortune 2 liter 32rb, Tropical 2 liter 33rb, Filma 1 liter 17rb. Semua ready di Gresik",
            "url": "https://www.facebook.com/groups/jualbelisembako/posts/10234567891235202",
            "scraped_at": "2026-06-10T18:05:00",
            "raw_location": None,
            "language": "id",
            "query_strategy": "keyword",
        },
        {
            "id": str(uuid.uuid4()),
            "source": "facebook",
            "source_id": "10234567891235580",
            "raw_text": "Minyak Goreng Bimoli 2 Liter ready stock area Surabaya, PM dulu ya kak buat harga & stok terbaru",
            "url": "https://www.facebook.com/groups/jualbelisembako/posts/10234567891235580",
            "scraped_at": "2026-06-11T11:30:00",
            "raw_location": None,
            "language": "id",
            "query_strategy": "keyword",
        },
    ])
