from src.ingest import facebook, facebook_marketplace, indotrading, tokopedia_grosir, shopee_grosir, twitter

# Registry semua source ingest. Tiap module nyediain fungsi ingest(subject) -> pd.DataFrame
# yang formatnya udah sesuai bronze_schema.
SOURCES = {
    "facebook": facebook.ingest,
    "facebook_marketplace": facebook_marketplace.ingest,
    "indotrading": indotrading.ingest,
    "tokopedia_grosir": tokopedia_grosir.ingest,
    "shopee_grosir": shopee_grosir.ingest,
    "twitter": twitter.ingest,
}
