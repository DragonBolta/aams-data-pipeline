import numpy as np
import pandas as pd
import pytest

from src.clean import clean


@pytest.fixture
def raw_survey_data():
    data = {
        "Timestamp": ["2021-02-17 10:00:00", "2020-11-01 12:30:00", "2021-03-05", "Not a date", "2022-01-01",
                      "2020/01/01"],
        "How old are you?": ["under 18", "45-50", "30", "25", "30", "22"],
        "What industry do you work in?": ["Tech", "Finance", "N/A", "Marketing", "HR", "Education"],
        "Job title": [" data engineer ", "Analyst", "Unknown", "Manager", "Assistant", "Teacher"],
        "If your job title needs additional context, please clarify here:": ["", "", "", "", "", ""],
        "What is your annual salary? (You'll indicate the currency in a later question. If you are part-time or hourly, please enter an annualized equivalent -- what you would earn if you worked the job 40 hours a week, 52 weeks a year.)": [
            "$100,000", "85000", "0", "90000", "40000", "30000"],
        "How much additional monetary compensation do you get, if any (for example, bonuses or overtime in an average year)? Please only include monetary compensation here, not the value of benefits.": [
            "5,000", "0", "0", "2000", "1000", "0"],
        "Please indicate the currency": ["usd", "cad", "USD", "EUR", "GBP", "USD"],
        "If your income needs additional context, please provide it here:": ["", "", "", "", "", ""],
        "What country do you work in?": ["United States", "Canada", "Italy", "ZZZ", "UK", "Germany"],
        "If you're in the U.S., what state do you work in?": ["New York", "FL", "", "", "", ""],
        "What city do you work in?": ["nyc", "Toronto", "Rome", "London", "Manchester", "Berlin"],
        "How many years of professional work experience do you have overall?": ["5 - 7 years", "1 year or less",
                                                                                "TOO MANY", "8 - 10 years",
                                                                                "11 - 20 years", "5 - 7 years"],
        "How many years of professional work experience do you have in your field?": ["2 - 4 years", "5 - 7 years",
                                                                                      "8 - 10 years", "11 - 20 years",
                                                                                      "5 - 7 years", "2 - 4 years"],
        "What is your highest level of education completed?": ["College degree", "Masters degree", "Masters degree",
                                                               "High School", "PHD", None],
        "What is your race? (Choose all that apply.)": ["White", "Asian", "Black", "White", "Hispanic", "White"],
        'What is your gender?': ["Woman", "Man", "Non-binary", "Woman", "Man", "Woman"]
    }
    return pd.DataFrame(data)


@pytest.fixture
def perfect_survey_data():
    data = {
        "Timestamp": ["2021-05-15 11:00:00"],
        "How old are you?": ["30-35"],
        "What industry do you work in?": ["Tech"],
        "Job title": [" Data Scientist "],
        "If your job title needs additional context, please clarify here:": [None],
        "What is your annual salary? (You'll indicate the currency in a later question. If you are part-time or hourly, please enter an annualized equivalent -- what you would earn if you worked the job 40 hours a week, 52 weeks a year.)": [
            "100000"],
        "How much additional monetary compensation do you get, if any (for example, bonuses or overtime in an average year)? Please only include monetary compensation here, not the value of benefits.": [
            "5000"],
        "Please indicate the currency": ["USD"],
        "If your income needs additional context, please provide it here:": [None],
        "What country do you work in?": ["United States"],
        "If you're in the U.S., what state do you work in?": ["New York"],
        "What city do you work in?": ["New York"],
        "How many years of professional work experience do you have overall?": ["5 - 7 years"],
        "How many years of professional work experience do you have in your field?": ["5 - 7 years"],
        "What is your highest level of education completed?": ["Masters degree"],
        "What is your race? (Choose all that apply.)": ["White"],
        'What is your gender?': ["Man"]
    }
    return pd.DataFrame(data)


@pytest.fixture
def no_timestamp_data(raw_survey_data):
    """Fixture to provide survey data missing the 'Timestamp' column."""
    return raw_survey_data.drop(columns=['Timestamp'])


def test_clean_standardizes_text(raw_survey_data):
    df, _ = clean(raw_survey_data)
    assert "age" in df.columns
    assert df.iloc[0]["job_title"] == "Data Engineer"
    assert df.iloc[0]["city"] == "Nyc"
    assert df.iloc[0]["currency"] == "USD"
    assert df.iloc[0]["us_state"] == "NY"


def test_salary_cleaning_handles_symbols(raw_survey_data):
    df, _ = clean(raw_survey_data)
    assert df.iloc[0]["salary"] == 100000
    assert isinstance(df.iloc[0]["salary"], (int, float, np.integer, np.floating))


def test_age_cleaning_handles_under_18(raw_survey_data):
    df, _ = clean(raw_survey_data)
    assert df.iloc[0]["age"] == 17
    assert df.iloc[1]["age"] == 45


def test_country_normalization_and_filtering(raw_survey_data):
    df, bad_rows = clean(raw_survey_data)

    assert len(df) == 2

    assert len(bad_rows) == 4

    reasons = bad_rows['drop_reason'].tolist()

    assert 'Missing Education (dropna)' in reasons
    assert 'Country Conversion Failed (ISO3=NaN)' in reasons
    assert 'Missing or Invalid professional_yoe (dropna)' in reasons
    assert 'Missing or Invalid Timestamp/Year (dropna)' in reasons


def test_year_extraction_and_filtering(raw_survey_data):
    pd.set_option('display.max_columns', None)
    df, bad_rows = clean(raw_survey_data)

    assert 'year' in df.columns
    assert df['year'].dtype == "Int64"

    assert df.iloc[0]['year'] == 2021
    assert df.iloc[1]['year'] == 2020


def test_clean_no_rows_dropped(perfect_survey_data):
    good_rows, bad_rows = clean(perfect_survey_data)

    assert len(good_rows) == 1
    assert good_rows.iloc

def test_clean_handles_missing_timestamp(no_timestamp_data):
    """Tests the scenario where the input data is missing the Timestamp column."""
    df, bad_rows = clean(no_timestamp_data)

    assert 'year' in df.columns
    assert df['year'].isna().all()
    assert df['year'].dtype == "Int64"

    assert len(bad_rows) == 3

    reasons = bad_rows['drop_reason'].tolist()
    assert 'Missing Education (dropna)' in reasons
    assert 'Country Conversion Failed (ISO3=NaN)' in reasons
    assert 'Missing or Invalid professional_yoe (dropna)' in reasons