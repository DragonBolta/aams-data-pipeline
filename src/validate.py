import logging
import great_expectations as gx
import pandas as pd

from src.clean import clean
from src.readers.csv_reader import read_csv


def validate(df):
    log = logging.getLogger(__name__)

    context = gx.get_context()
    data_source = context.data_sources.add_pandas("ask_a_manager_src")
    data_asset = data_source.add_dataframe_asset("survey_responses_raw")
    batch_definition = data_asset.add_batch_definition_whole_dataframe("whole_dataframe")
    batch = batch_definition.get_batch(batch_parameters={"dataframe": df})

    salary_column = 'Salary'

    df[salary_column] = df[salary_column].replace(',', '')
    df[salary_column] = pd.to_numeric(df[salary_column], errors="coerce")

    suite = context.suites.add(gx.ExpectationSuite(name="salary_survey_cleaning"))

    suite.add_expectation(
        gx.expectations.ExpectColumnValuesToNotBeNull(column="job_title")
    )

    suite.add_expectation(
        gx.expectations.ExpectColumnValuesToNotBeNull(column="salary")
    )

    suite.add_expectation(
        gx.expectations.ExpectColumnValuesToBeBetween(
            column=salary_column,
            min_value=10000,
            max_value=1000000
        )
    )

    suite.add_expectation(
        gx.expectations.ExpectColumnValuesToBeInSet(
            column="Please indicate the currency",
            value_set=["USD", "CAD", "GBP", "EUR", "AUD/NZD"]
        )
    )

    # suite.add_expectation

    validation_results = batch.validate(suite, result_format={"result_format": "COMPLETE"})

    unexpected_indices = set()

    for result in validation_results.results:
        if not result.success:
            indices = result.result.get("unexpected_index_list", [])
            unexpected_indices.update(indices)

            log.warning(f"Expectation '{result.expectation_config.type}' failed on {len(indices)} rows.")
        # else:
        #     indices = result.result.get()

    bad_index_list = list(unexpected_indices)

    bad_rows = df.iloc[bad_index_list]
    good_rows = df.drop(index=bad_index_list)

    print(f"Total rows processed: {len(df)}")
    print(f"Good rows: {len(good_rows)}")
    print(f"Bad rows: {len(bad_rows)}")

    return good_rows, bad_rows


if __name__ == "__main__":
    df = read_csv(filepath="../data/Ask A Manager Salary Survey 2021 (Responses) - Form Responses 1.csv")
    cleaned_df = clean(df)
    good, bad = validate(cleaned_df)