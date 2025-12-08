import logging
import great_expectations as gx
import pandas as pd


def validate(df):
    log = logging.getLogger(__name__)

    expectations_logger = logging.getLogger("great_expectations.expectations.expectation")

    expectations_logger.setLevel(logging.WARNING)

    context = gx.get_context()
    data_source = context.data_sources.add_pandas("ask_a_manager_src")
    data_asset = data_source.add_dataframe_asset("survey_responses_raw")

    batch_definition = data_asset.add_batch_definition_whole_dataframe("whole_dataframe")
    batch = batch_definition.get_batch(batch_parameters={"dataframe": df})

    suite = context.suites.add(gx.ExpectationSuite(name="salary_survey_schema_and_logic"))

    full_schema = {
        "job_context": {"type": "object", "max_len": 255},
        "industry": {"type": "object", "max_len": 50},
        "job_title": {"type": "object", "max_len": 100},
        "currency": {"type": "object", "max_len": 7},
        "income_context": {"type": "object", "max_len": 100},
        "country": {"type": "object", "max_len": 3},
        "us_state": {"type": "object", "max_len": 27},
        "city": {"type": "object", "max_len": 52},
        "year": {"type": "int64", "max_len": None},
        "age": {"type": "int64", "max_len": None},
        "salary": {"type": "int64", "max_len": None},
        "bonus": {"type": "int64", "max_len": None},
    }

    for col, rules in full_schema.items():
        suite.add_expectation(gx.expectations.ExpectColumnToExist(column=col))

        suite.add_expectation(
            gx.expectations.ExpectColumnValuesToBeOfType(column=col, type_=rules["type"])
        )

        if rules["max_len"]:
            suite.add_expectation(
                gx.expectations.ExpectColumnValueLengthsToBeBetween(
                    column=col, min_value=0, max_value=rules["max_len"]
                )
            )

    suite.add_expectation(
        gx.expectations.ExpectColumnValuesToNotBeNull(column="job_title")
    )

    suite.add_expectation(
        gx.expectations.ExpectColumnValuesToNotBeNull(column="salary")
    )
    suite.add_expectation(
        gx.expectations.ExpectColumnValuesToBeBetween(
            column="salary",
            min_value=10_000,
            max_value=1_000_000
        )
    )

    suite.add_expectation(
        gx.expectations.ExpectColumnValuesToBeBetween(
            column="year",
            min_value=2015,
            max_value=2030
        )
    )

    suite.add_expectation(
        gx.expectations.ExpectColumnValuesToBeInSet(
            column="currency",
            value_set=["USD", "CAD", "GBP", "EUR", "AUD/NZD"]
        )
    )

    suite.add_expectation(
        gx.expectations.ExpectColumnValuesToBeBetween(
            column="age",
            min_value=18,
            max_value=100
        )
    )

    suite.add_expectation(
        gx.expectations.ExpectColumnValuesToMatchRegex(
            column="country",
            regex=r"^[A-Z]{3}$"
        )
    )

    suite.add_expectation(
        gx.expectations.ExpectColumnValuesToNotBeNull(column="industry")
    )

    suite.add_expectation(
        gx.expectations.ExpectColumnValuesToNotBeInSet(column="currency", value_set=["Other"])
    )

    suite.add_expectation(
        gx.expectations.ExpectColumnValuesToNotBeNull(column="professional_yoe")
    )

    suite.add_expectation(
        gx.expectations.ExpectColumnValuesToNotBeNull(column="industry_yoe")
    )

    validation_results = batch.validate(suite, result_format={"result_format": "COMPLETE"})

    unexpected_indices = set()

    for result in validation_results.results:
        if not result.success:
            indices = result.result.get("unexpected_index_list", [])
            unexpected_indices.update(indices)
            log.warning(
                f"Expectation '{result.expectation_config.type}' on column '{result.expectation_config.kwargs.get('column')}' failed on {len(indices)} rows.")

    bad_index_list = list(unexpected_indices)

    bad_rows = df.iloc[bad_index_list]
    good_rows = df.drop(index=bad_index_list)

    print(f"Total rows processed: {len(df)}")
    print(f"Good rows: {len(good_rows)}")
    print(f"Bad rows: {len(bad_rows)}")

    return good_rows, bad_rows


if __name__ == "__main__":
    from src.readers.csv_reader import read_csv
    from src.clean import clean

    df = read_csv(filepath="../data/Ask A Manager Salary Survey 2021 (Responses) - Form Responses 1.csv")
    cleaned_df = clean(df)
    good, bad = validate(cleaned_df)