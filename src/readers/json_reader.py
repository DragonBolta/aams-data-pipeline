import pandas as pd
import logging
import os


def read_json(filepath, rows=None):
    log = logging.getLogger(__name__)

    if not os.path.exists(filepath):
        log.error(f"File not found: {filepath}")
        raise FileNotFoundError(f"File not found: {filepath}")

    try:
        df = pd.read_json(filepath, orient='records', lines=True, nrows=rows)
        log.info(f"Read {len(df)} rows from JSON: {filepath}")
        return df
    except Exception as e:
        log.error(f"Failed to read JSON {filepath}: {e}")
        raise e