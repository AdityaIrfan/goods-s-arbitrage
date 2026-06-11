import uuid
import pandas as pd

# TODO: ganti dengan scraping asli (lihat task ingest scrapers).
# Untuk sekarang return dummy data yang merepresentasikan struktur listing
# Facebook Marketplace, biar tahap parse/normalize/dst bisa di-test pakai data
# yang mirip aslinya.
def ingest(subject: str) -> pd.DataFrame:
    return pd.DataFrame([
        {
            "id": str(uuid.uuid4()),
            "source": "facebook_marketplace",
            "source_id": "1122334455667788",
            "raw_text": "Minyak Goreng Curah 5 Liter - Rp 95.000 - Lokasi: Mojokerto",
            "url": "https://www.facebook.com/marketplace/item/1122334455667788",
            "scraped_at": "2026-06-08T11:30:00",
            "raw_location": "Mojokerto",
            "language": "id",
            "query_strategy": "keyword",
        },
        {
            "id": str(uuid.uuid4()),
            "source": "facebook_marketplace",
            "source_id": "1122334455668120",
            "raw_text": "Bimoli Spesial 2 Liter (1 Karton isi 6 botol) - Rp 198.000 per karton - Malang",
            "url": "https://www.facebook.com/marketplace/item/1122334455668120",
            "scraped_at": "2026-06-09T16:05:00",
            "raw_location": "Malang",
            "language": "id",
            "query_strategy": "keyword",
        },
        {
            "id": str(uuid.uuid4()),
            "source": "facebook_marketplace",
            "source_id": "1122334455668455",
            "raw_text": "Minyak goreng Sania jeriken 18 liter - Rp 320.000 - Surabaya, ambil sendiri",
            "url": "https://www.facebook.com/marketplace/item/1122334455668455",
            "scraped_at": "2026-06-10T08:50:00",
            "raw_location": "Surabaya",
            "language": "id",
            "query_strategy": "keyword",
        },
        {
            "id": str(uuid.uuid4()),
            "source": "facebook_marketplace",
            "source_id": "1122334455668790",
            "raw_text": "Jual Minyak Goreng Curah 10 Dus, harga 500rb, COD area Malang",
            "url": "https://www.facebook.com/marketplace/item/1122334455668790",
            "scraped_at": "2026-06-11T09:15:00",
            "raw_location": "Malang",
            "language": "id",
            "query_strategy": "keyword",
        },
    ])
