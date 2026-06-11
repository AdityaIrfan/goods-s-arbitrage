import pandas as pd

from src.config.loader import load_subject_config
from src.storage import gold


def analyze_listings(silver_data: pd.DataFrame, bronze_data: pd.DataFrame, subject: str) -> dict:
    config = load_subject_config(subject)
    estimated_shipping = config.get("analyze", {}).get("estimated_shipping_per_liter", 0.0)

    merged = _merge_with_bronze(silver_data, bronze_data)

    price_spread = _price_spread_summary(merged)
    opportunity_pairs = _opportunity_pairs(merged, estimated_shipping)
    brand_summary = _brand_summary(merged)

    price_spread_file = gold.save_price_spread(subject, price_spread)
    opportunity_pairs_file = gold.save_opportunity_pairs(subject, opportunity_pairs)
    brand_summary_file = gold.save_brand_summary(subject, brand_summary)

    return {
        "price_spread_rows": len(price_spread),
        "opportunity_pairs_rows": len(opportunity_pairs),
        "brand_summary_rows": len(brand_summary),
        "price_spread_file": price_spread_file,
        "opportunity_pairs_file": opportunity_pairs_file,
        "brand_summary_file": brand_summary_file,
    }


def _merge_with_bronze(silver_data: pd.DataFrame, bronze_data: pd.DataFrame) -> pd.DataFrame:
    bronze_meta = bronze_data[["id", "source", "scraped_at"]].rename(columns={"id": "bronze_id"})
    merged = silver_data.merge(bronze_meta, on="bronze_id", how="left")

    merged = merged[merged["price_per_liter"].notna()].copy()
    merged["date"] = merged["scraped_at"].str.slice(0, 10)

    return merged


def _trace_fields(group: pd.DataFrame) -> dict:
    lowest = group.loc[group["price_per_liter"].idxmin()]
    highest = group.loc[group["price_per_liter"].idxmax()]

    return {
        "lowest_price_silver_id": lowest["id"],
        "lowest_price_bronze_id": lowest["bronze_id"],
        "highest_price_silver_id": highest["id"],
        "highest_price_bronze_id": highest["bronze_id"],
        "silver_ids": list(group["id"]),
        "bronze_ids": sorted(set(group["bronze_id"])),
    }


def _price_spread_summary(merged: pd.DataFrame) -> pd.DataFrame:
    rows = []

    grouped = merged.groupby(["product_type", "brand", "city", "date", "source"], dropna=False)
    for (product_type, brand, city, date, source), group in grouped:
        rows.append({
            "product_type": product_type,
            "brand": brand,
            "city": city,
            "date": date,
            "source": source,
            "min_price_per_liter": group["price_per_liter"].min(),
            "max_price_per_liter": group["price_per_liter"].max(),
            "avg_price_per_liter": group["price_per_liter"].mean(),
            "listing_count": len(group),
            **_trace_fields(group),
        })

    return pd.DataFrame(rows, columns=list(gold.price_spread_schema.columns.keys()))


def _brand_summary(merged: pd.DataFrame) -> pd.DataFrame:
    rows = []

    grouped = merged.groupby(["product_type", "brand", "date"], dropna=False)
    for (product_type, brand, date), group in grouped:
        rows.append({
            "product_type": product_type,
            "brand": brand,
            "date": date,
            "min_price_per_liter": group["price_per_liter"].min(),
            "max_price_per_liter": group["price_per_liter"].max(),
            "avg_price_per_liter": group["price_per_liter"].mean(),
            "city_count": group["city"].nunique(),
            "listing_count": len(group),
            **_trace_fields(group),
        })

    return pd.DataFrame(rows, columns=list(gold.brand_summary_schema.columns.keys()))


def _opportunity_pairs(merged: pd.DataFrame, estimated_shipping: float) -> pd.DataFrame:
    rows = []

    grouped = merged.groupby(["product_type", "brand", "date"], dropna=False)
    for (product_type, brand, date), group in grouped:
        cities = group.dropna(subset=["city"])
        if cities["city"].nunique() < 2:
            continue

        cheapest = cities.loc[cities["price_per_liter"].idxmin()]
        priciest = cities.loc[cities["price_per_liter"].idxmax()]

        if cheapest["city"] == priciest["city"]:
            continue

        price_diff = priciest["price_per_liter"] - cheapest["price_per_liter"]

        rows.append({
            "product_type": product_type,
            "brand": brand,
            "date": date,
            "cheap_city": cheapest["city"],
            "cheap_price_per_liter": cheapest["price_per_liter"],
            "cheap_source": cheapest["source"],
            "expensive_city": priciest["city"],
            "expensive_price_per_liter": priciest["price_per_liter"],
            "expensive_source": priciest["source"],
            "price_diff_per_liter": price_diff,
            "estimated_shipping_per_liter": float(estimated_shipping),
            "net_diff_per_liter": price_diff - estimated_shipping,
            "lowest_price_silver_id": cheapest["id"],
            "lowest_price_bronze_id": cheapest["bronze_id"],
            "highest_price_silver_id": priciest["id"],
            "highest_price_bronze_id": priciest["bronze_id"],
            "silver_ids": list(cities["id"]),
            "bronze_ids": sorted(set(cities["bronze_id"])),
        })

    return pd.DataFrame(rows, columns=list(gold.opportunity_pairs_schema.columns.keys()))
