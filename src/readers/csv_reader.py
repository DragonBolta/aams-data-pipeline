import datetime
import logging

import pandas


def read_csv(filepath="../../data/Ask A Manager Salary Survey 2021 (Responses) - Form Responses 1.csv", rows=None):
    log = logging.getLogger(__name__)
    start_time = datetime.datetime.now()
    df = pandas.read_csv(filepath, nrows=rows)
    end_time = datetime.datetime.now()
    log.info(f"Read {len(df)} rows from csv in {(end_time - start_time).total_seconds()} seconds ({len(df)/(end_time - start_time).total_seconds()} rows per second)")

    return df

if __name__ == "__main__":
    read_csv()