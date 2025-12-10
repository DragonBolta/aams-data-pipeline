import argparse

from dotenv import load_dotenv

from src.load import setup_db_schema
from src.readers.csv_reader import read_csv
from src.etl import etl

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

    setup_db_schema()

    args = parser.parse_args()
    filepath = args.filepath

    print(f"Reading CSV from: {filepath}")
    df = read_csv(filepath=filepath)
    etl(df)



if __name__ == "__main__":
    main()