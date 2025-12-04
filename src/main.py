if __name__ == "__main__":
    from src.readers.csv_reader import read_csv
    from src.clean import clean
    from src.validate import validate
    from src.load import load_into_db, load_errors

    df = read_csv(filepath="../data/Ask A Manager Salary Survey 2021 (Responses) - Form Responses 1.csv")
    good_rows, bad_rows = clean(df)

    if not bad_rows.empty:
        print(f"Capturing {len(bad_rows)} invalid rows...")
        load_errors(bad_rows, reason="Failed to clean")

    good_rows, bad_rows = validate(good_rows)

    print(f"Loading {len(good_rows)} valid rows...")
    load_into_db(good_rows)

    if not bad_rows.empty:
        print(f"Capturing {len(bad_rows)} invalid rows...")
        load_errors(bad_rows, reason="Schema/Validation Mismatch")