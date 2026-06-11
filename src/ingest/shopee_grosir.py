import uuid
import pandas as pd

# TODO: ganti dengan scraping asli (lihat task ingest scrapers).
# Untuk sekarang return dummy data yang merepresentasikan struktur & gaya bahasa
# listing toko grosir di Shopee, biar tahap parse/normalize/dst bisa di-test
# pakai data yang mirip aslinya.
def ingest(subject: str) -> pd.DataFrame:
    return pd.DataFrame([
        {
            "id": str(uuid.uuid4()),
            "source": "shopee_grosir",
            "source_id": "9912345678",
            "raw_text": "[GROSIR] Minyak Goreng Tropical 2L x 6 botol per dus - Rp 210.000/dus - Gudang Bandung, gratis ongkir",
            "url": "https://shopee.co.id/product/9912345678/minyak-goreng-tropical-2l-grosir",
            "scraped_at": "2026-06-08T14:25:00",
            "raw_location": "Bandung",
            "language": "id",
            "query_strategy": "kategori",
        },
        {
            "id": str(uuid.uuid4()),
            "source": "shopee_grosir",
            "source_id": "9912345901",
            "raw_text": "Minyak Goreng Curah 1 Kg - Rp 16.000/kg - Lokasi Jogja, COD area kota",
            "url": "https://shopee.co.id/product/9912345901/minyak-goreng-curah-1kg",
            "scraped_at": "2026-06-09T17:50:00",
            "raw_location": "Jogja",
            "language": "id",
            "query_strategy": "kategori",
        },
        {
            "id": str(uuid.uuid4()),
            "source": "shopee_grosir",
            "source_id": "9912346205",
            "raw_text": "Bimoli 2 Liter Kemasan Pouch - Rp 34.500/pcs - Toko Hemat Jaya, Surabaya",
            "url": "https://shopee.co.id/product/9912346205/bimoli-2-liter-pouch",
            "scraped_at": "2026-06-10T19:35:00",
            "raw_location": "Surabaya",
            "language": "id",
            "query_strategy": "kategori",
        },
    ])
