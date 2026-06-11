import re
import uuid
from typing import List

from pandas import DataFrame

from src.config.loader import load_subject_config


class IndonesiaParser:
    def __init__(self, formats: list[str], data: DataFrame, subject: str):
        self.data = data
        self.formats = formats
        self.config = load_subject_config(subject)

    def parse(self) -> List[dict]:
        result = []
        for _, row in self.data.iterrows():
            bronze_id = row["id"]
            raw_text = row["raw_text"]

            for segment in self._split_segments(raw_text):
                extract = {
                    "id": str(uuid.uuid4()),
                    "bronze_id": bronze_id,
                }
                matches = {}

                for f in self.formats:
                    match f:
                        case "price":
                            price_matches = self._extract_price(segment)
                            matches["price"] = price_matches
                            extract["price"] = self._price_to_numeric(price_matches[0]) if price_matches else None
                        case "currency":
                            extract["currency"] = self._extract_currency(segment)
                        case "brand":
                            brand_matches = self._extract_brand(segment)
                            matches["brand"] = brand_matches
                            extract["brand"] = brand_matches[0] if brand_matches else None
                        case "location":
                            location_matches = self._extract_location(raw_text)
                            matches["location"] = location_matches
                            extract["location"] = location_matches[0] if location_matches else None
                        case "unit-quantity":
                            unit_quantity = self._extract_unit_quantities(segment)
                            matches["unit-quantity"] = unit_quantity
                            extract["unit-quantity"] = unit_quantity

                extract["parse_confidence"] = self._score_confidence(matches)
                result.append(extract)

        return result

    def _split_segments(self, text: str) -> list[str]:
        # Post bisa berisi banyak item (multi-brand) dalam satu raw_text,
        # misal "Fortune 2 liter 32rb, Tropical 2 liter 33rb". Tiap brand
        # jadi penanda awal item baru, biar masing-masing dapet baris silver sendiri.
        matches = list(re.finditer(self._brand_pattern(), text, re.IGNORECASE))

        if len(matches) <= 1:
            return [text]

        segments = []
        for i, m in enumerate(matches):
            start = 0 if i == 0 else m.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            segments.append(text[start:end])

        return segments

    def _brand_pattern(self) -> str:
        brands = self.config["parse"]["brands"]
        return r'\b(' + '|'.join(re.escape(b) for b in brands) + r')\b'

    @staticmethod
    def _extract_price(text: str) -> list[str]:
        patterns = [
            r'\b\d{1,3}(?:[.,]\d{1,3})*(?:\s*(?:rb|ribu|k))\b',  # 185rb, 18.5rb, 185k, 185ribu
            r'\b\d{1,3}(?:[.,]\d{3})+\b',                          # 185.000 / 185,000
        ]
        results = []
        for p in patterns:
            results += re.findall(p, text, re.IGNORECASE)
        return list(dict.fromkeys(results))

    @staticmethod
    def _price_to_numeric(price_str: str) -> float | None:
        if not price_str:
            return None

        s = price_str.strip().lower()

        multiplier = 1
        suffix_match = re.search(r'(rb|ribu|k)\s*$', s)
        if suffix_match:
            multiplier = 1000
            s = s[:suffix_match.start()].strip()

        # ".000" / ",000" dianggap pemisah ribuan, dihapus
        s = re.sub(r'[.,](\d{3})\b', r'\1', s)
        # sisa koma dianggap titik desimal
        s = s.replace(",", ".")

        try:
            return float(s) * multiplier
        except ValueError:
            return None

    @staticmethod
    def _extract_currency(text: str) -> str:
        # Semua sumber berbahasa Indonesia di subject ini transaksi pakai Rupiah
        return "IDR"

    def _extract_unit_quantities(self, text: str) -> dict:
        units = self.config["parse"]["units"]
        unit_alternatives = '|'.join(re.escape(u) for u in units.keys())
        # Angka + satuan, tanpa wajib spasi (biar "2L" ke-detect juga)
        pattern = r'([0-9]+(?:[.,][0-9]+)?)\s*(' + unit_alternatives + r')\b'

        matches = re.findall(pattern, text, re.IGNORECASE)

        result = {}
        for angka_str, satuan in matches:
            try:
                angka_clean = angka_str.replace(",", ".")
                satuan_clean = units.get(satuan.lower(), satuan.lower())
                result[satuan_clean] = float(angka_clean)
            except ValueError:
                continue

        return result

    def _extract_brand(self, text: str) -> list[str]:
        return list(dict.fromkeys(re.findall(self._brand_pattern(), text, re.IGNORECASE)))

    def _extract_location(self, text: str) -> list[str]:
        locations = self.config["parse"]["locations"]
        pattern = r'\b(' + '|'.join(re.escape(l) for l in locations) + r')\b'
        return list(dict.fromkeys(re.findall(pattern, text, re.IGNORECASE)))

    @staticmethod
    def _score_confidence(matches: dict) -> str:
        price = matches.get("price")
        units = matches.get("unit-quantity")
        brands = matches.get("brand")
        locations = matches.get("location")

        if (price is not None and len(price) == 0) or (units is not None and len(units) == 0):
            return "low"
        if (price is not None and len(price) > 1) or (brands is not None and len(brands) > 1):
            return "low"
        if (brands is not None and len(brands) == 0) or (locations is not None and len(locations) == 0):
            return "medium"
        return "high"
