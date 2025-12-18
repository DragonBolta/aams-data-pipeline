import datetime
import logging
import pyspark


def read_csv(spark, filepath="../../data/Ask A Manager Salary Survey 2021 (Responses) - Form Responses 1.csv"):
    if not spark:
        raise Exception("Invalid spark session")

    log = logging.getLogger(__name__)
    start_time = datetime.datetime.now()

    ds = (spark.read
          .option("header", "true")
          .option("escape", "\"")
          .option("quote", "\"")
          .csv(filepath).limit(200))

    end_time = datetime.datetime.now()
    duration = (end_time - start_time).total_seconds()

    rows_per_sec = ds.count() / duration if duration > 0 else ds.count()

    log.info(f"Read {ds.count()} rows from csv in {duration} seconds ({rows_per_sec} rows per second)")

    return ds
