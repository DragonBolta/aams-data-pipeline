import argparse
from src.readers.csv_reader import read_csv
from src.clean import clean
from src.validate import validate
from src.load import load_into_db, load_errors


def main():
    parser = argparse.ArgumentParser(
        description="ETL script to process salary survey data.",
        formatter_class=argparse.RawTextHelpFormatter
    )

    parser.add_argument(
        "filepath",
        nargs="?",
        default="../data/Ask A Manager Salary Survey 2021 (Responses) - Form Responses 1.csv",
        help="The path to the CSV file to be processed.\n"
             "Defaults to: ../data/Ask A Manager Salary Survey 2021 (Responses) - Form Responses 1.csv"
    )

    args = parser.parse_args()
    filepath = args.filepath

    print(f"Reading CSV from: {filepath}")
    df = read_csv(filepath=filepath)
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


if __name__ == "__main__":
    main()