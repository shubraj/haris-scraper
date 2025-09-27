import pandas as pd
from app1.table import get_table


def scrape_instruments(instrument_keys, instrument_types, start_date, end_date):
    """Scrape instruments for selected keys and return combined DataFrame."""
    all_results = []

    # Group keys by code (avoid scraping duplicates)
    code_to_keys = {}
    for key in instrument_keys:
        code = instrument_types[key]
        code_to_keys.setdefault(code, []).append(key)

    for code, keys in code_to_keys.items():
        df = get_table(code, start_date, end_date)
        if not df.empty:
            df["Instrument Type"] = ", ".join(keys)
            all_results.append(df)

    if all_results:
        return pd.concat(all_results, ignore_index=True)
    return None
