import pandas as pd
import pytest
import numpy as np
from src.clean import clean
from src.clean import standardize_us_state


@pytest.fixture
def raw_survey_data():
    data = {
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

    assert len(df) == 3

    assert len(bad_rows) == 3

    reasons = bad_rows['drop_reason'].tolist()

    assert 'Missing Education (dropna)' in reasons
    assert 'Country Conversion Failed (ISO3=NaN)' in reasons
    assert 'Missing or Invalid professional_yoe (dropna)' in reasons

    assert 'Country Code Not ISO3 Format' not in reasons
    assert 'Missing or Invalid industry_yoe (dropna)' not in reasons


def test_clean_no_rows_dropped(perfect_survey_data):
    good_rows, bad_rows = clean(perfect_survey_data)

    assert len(good_rows) == 1
    assert bad_rows.empty


def test_standardize_us_state_helper():
    assert standardize_us_state("NY") == "NY"
    assert standardize_us_state("new york") == "NY"
    assert standardize_us_state("not_a_state") == "NOT_A_STATE"
    assert standardize_us_state("") is None
    assert standardize_us_state(None) is None