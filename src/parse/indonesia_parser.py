import re
from typing import List

from pandas import Series

class IndonesiaParser:
    def __init__(self, formats: list[str], raw_text: Series):
        self.raw_text = raw_text
        self.formats = formats

    def parse(self) -> List:
        result = []
        for text in self.raw_text:
            extract = dict()

            for f in self.formats:
                match f:
                    case "price":
                        extract["price"] = self._extract_price(text)
                    case "brand":
                        extract["brand"] = self._extract_brand(text)
                    case "location":
                        extract["location"] = self._extract_location(text)
                    case "unit-quantity":
                        unit_quantity = self._extract_unit_quantities(text)
                        extract["unit-quantity"] = unit_quantity
            result.append(extract)

        return result

    @staticmethod
    def _extract_price(text: str) -> list[str]:
        patterns = [
            r'\b\d{1,3}(?:[.,]\d{3})*(?:\s*(?:rb|ribu|k))\b',  # 185rb, 185k, 185ribu
            r'\b\d{1,3}(?:[.,]\d{3})+\b',                        # 185.000 / 185,000
        ]
        results = []
        for p in patterns:
            results += re.findall(p, text, re.IGNORECASE)
        return list(set(results))

    @staticmethod
    def _extract_unit_quantities(text: str) -> dict:
        # 1. Masukkan list satuan lo ke dalam regex pola pasangan (Angka + Satuan)
        # Kita pakai tanda kurung di angka dan di satuannya biar bisa dipisah
        pattern = r'([0-9.,]+)\s*\b(karton|jeriken|jrk|liter|literan|lt|kg|kilogram|pcs|dus|botol|sachet)\b'

        # findall bakal ngembalikin list of tuple: [('2', 'liter'), ('10', 'dus')]
        matches = re.findall(pattern, text, re.IGNORECASE)

        result = {}
        for angka_str, satuan in matches:
            try:
                # Standarisasi koma desimal gaya Indonesia (1,5 -> 1.5)
                angka_clean = angka_str.replace(",", ".")
                # Standarisasi nama satuan biar seragam (misal: lt jadi liter)
                satuan_clean = satuan.lower()
                if satuan_clean == 'lt' or satuan_clean == 'literan' : satuan_clean = 'liter'
                if satuan_clean == 'jrk': satuan_clean = 'jeriken'
                if satuan_clean == 'kilogram': satuan_clean = 'kg'

                # Simpan ke dictionary: {'liter': 2.0, 'dus': 10.0}
                result[satuan_clean] = float(angka_clean)
            except ValueError:
                continue

        return result


    @staticmethod
    def _extract_brand(text: str) -> list[str]:
        pattern = r'\b(bimoli|sania|tropical|tropicana|filma|curah|fortune)\b'
        return list(set(re.findall(pattern, text, re.IGNORECASE)))


    @staticmethod
    def _extract_location(text: str) -> list[str]:
        pattern = r'\b(surabaya|sidoarjo|gresik|mojokerto|malang|jakarta|bandung|semarang|jogja|yogyakarta)\b'
        return list(set(re.findall(pattern, text, re.IGNORECASE)))