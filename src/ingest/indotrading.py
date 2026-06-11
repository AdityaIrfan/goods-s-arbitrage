import uuid
import pandas as pd

# TODO: ganti dengan scraping asli (lihat task ingest scrapers).
# Untuk sekarang return dummy data yang merepresentasikan struktur & gaya bahasa
# listing B2B/grosir di Indotrading, biar tahap parse/normalize/dst bisa di-test
# pakai data yang mirip aslinya.
def ingest(subject: str) -> pd.DataFrame:
    return pd.DataFrame([
        {
            "id": str(uuid.uuid4()),
            "source": "indotrading",
            "source_id": "PR-118820",
            "raw_text": "Jual Minyak Goreng Curah Kemasan Jerigen 18 Liter - Distributor Resmi Surabaya, harga grosir Rp 315.000/jerigen, minimal order 10 jerigen",
            "url": "https://www.indotrading.com/product/minyak-goreng-curah-jerigen-18-liter-PR118820.aspx",
            "scraped_at": "2026-06-08T07:45:00",
            "raw_location": "Surabaya, Jawa Timur",
            "language": "id",
            "query_strategy": "keyword",
        },
        {
            "id": str(uuid.uuid4()),
            "source": "indotrading",
            "source_id": "PR-118955",
            "raw_text": "Distributor Minyak Goreng Fortune 2 Liter, kemasan 1 dus isi 6 pcs, harga Rp 195.000/dus, area pengiriman Jawa Timur",
            "url": "https://www.indotrading.com/product/minyak-goreng-fortune-2-liter-PR118955.aspx",
            "scraped_at": "2026-06-09T10:20:00",
            "raw_location": "Sidoarjo, Jawa Timur",
            "language": "id",
            "query_strategy": "keyword",
        },
        {
            "id": str(uuid.uuid4()),
            "source": "indotrading",
            "source_id": "PR-119087",
            "raw_text": "Supplier Minyak Goreng Tropical Kemasan Botol 1 Liter, harga Rp 18.500/botol, stok tersedia di Jakarta",
            "url": "https://www.indotrading.com/product/minyak-goreng-tropical-1-liter-PR119087.aspx",
            "scraped_at": "2026-06-10T13:10:00",
            "raw_location": "Jakarta",
            "language": "id",
            "query_strategy": "keyword",
        },
    ])
