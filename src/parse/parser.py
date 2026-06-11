from typing import List

from pandas import DataFrame

from src.parse.indonesia_parser import IndonesiaParser

def parse_raw_text(formats: list[str], data: DataFrame, lang: str, subject: str) -> List[dict]:
    match lang:
        case "indonesia":
            return IndonesiaParser(formats, data, subject).parse()
        case _:
            raise Exception(f"Unknown language: {lang}")
