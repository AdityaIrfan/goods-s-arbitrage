import uuid
import pandas as pd

# TODO: ganti dengan scraping asli (lihat task ingest scrapers).
# Untuk sekarang return dummy data yang merepresentasikan struktur & gaya bahasa
# listing toko grosir di Tokopedia, biar tahap parse/normalize/dst bisa di-test
# pakai data yang mirip aslinya.
def ingest(subject: str) -> pd.DataFrame:
    return pd.DataFrame([
        {
            "id": str(uuid.uuid4()),
            "source": "tokopedia_grosir",
            "source_id": "8801234567",
            "raw_text": "Minyak Goreng Bimoli 1 Liter - 1 Dus isi 12 pcs - Rp 204.000/dus - Toko Sembako Makmur, Jakarta Barat",
            "url": "https://www.tokopedia.com/sembakomakmur/minyak-goreng-bimoli-1-liter-1-dus",
            "scraped_at": "2026-06-08T12:00:00",
            "raw_location": "Jakarta Barat",
            "language": "id",
            "query_strategy": "kategori",
        },
        {
            "id": str(uuid.uuid4()),
            "source": "tokopedia_grosir",
            "source_id": "8801234812",
            "raw_text": "Minyak Goreng Sania 2 Liter Botol - Rp 37.000/botol - Toko Grosir Sentosa, Bandung",
            "url": "https://www.tokopedia.com/grosirsentosa/minyak-goreng-sania-2-liter-botol",
            "scraped_at": "2026-06-09T09:30:00",
            "raw_location": "Bandung",
            "language": "id",
            "query_strategy": "kategori",
        },
        {
            "id": str(uuid.uuid4()),
            "source": "tokopedia_grosir",
            "source_id": "8801235044",
            "raw_text": "Paket Minyak Goreng Filma 5 Liter Jerigen - Rp 92.500/jeriken - Gudang Semarang",
            "url": "https://www.tokopedia.com/gudangsemarang/minyak-goreng-filma-5-liter-jerigen",
            "scraped_at": "2026-06-10T15:45:00",
            "raw_location": "Semarang",
            "language": "id",
            "query_strategy": "kategori",
        },
    ])
