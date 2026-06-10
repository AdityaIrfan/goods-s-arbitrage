from typing import List
from pandas import Series

from src.parse.indonesia_parser import IndonesiaParser

def parse_raw_text(formats: list[str], raw_text: Series, lang: str) -> List:
    match lang:
        case "indonesia":
            return IndonesiaParser(formats, raw_text).parse()
        case _:
            raise Exception(f"Unknown language: {lang}")
