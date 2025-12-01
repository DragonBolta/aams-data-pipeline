import datetime
import logging
import pandas


def read_csv(filepath="../../data/Ask A Manager Salary Survey 2021 (Responses) - Form Responses 1.csv", rows=None):
    log = logging.getLogger(__name__)
    start_time = datetime.datetime.now()

    df = pandas.read_csv(filepath, nrows=rows)

    end_time = datetime.datetime.now()
    duration = (end_time - start_time).total_seconds()

    rows_per_sec = len(df) / duration if duration > 0 else len(df)

    log.info(f"Read {len(df)} rows from csv in {duration} seconds ({rows_per_sec} rows per second)")

    return df