from src.clean import clean
from src.validate import validate
from src.load import load_into_db, load_errors

def etl(spark, df):
    good_rows, bad_rows = clean(spark, df)

    if not bad_rows.isEmpty():
        print(f"Capturing {bad_rows.count()} invalid rows (Failed to clean)...")
        bad_rows.show()
        load_errors(bad_rows, reason="Failed to clean")

    good_rows, bad_rows = validate(good_rows)

    if not good_rows.isEmpty():
        print(f"Loading {good_rows.count()} valid rows...")
        load_into_db(good_rows)

    if not bad_rows.isEmpty():
        print(f"Capturing {bad_rows.count()} invalid rows (Schema/Validation Mismatch)...")
        load_errors(bad_rows, reason="Schema/Validation Mismatch")