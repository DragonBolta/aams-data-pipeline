from src.clean import clean
from src.validate import validate
from src.load import load_into_db, load_errors

def etl(df):
    good_rows, bad_rows = clean(df)

    if not bad_rows.empty:
        print(f"Capturing {len(bad_rows)} invalid rows (Failed to clean)...")
        load_errors(bad_rows, reason="Failed to clean")

    good_rows, bad_rows = validate(good_rows)

    print(f"Loading {len(good_rows)} valid rows...")
    load_into_db(good_rows)

    if not bad_rows.empty:
        print(f"Capturing {len(bad_rows)} invalid rows (Schema/Validation Mismatch)...")
        load_errors(bad_rows, reason="Schema/Validation Mismatch")