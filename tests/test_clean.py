import pandas as pd
import pytest
import numpy as np
from src.clean import clean


@pytest.fixture
def raw_survey_data():
    data = {
        "How old are you?": ["under 18", "45-50", "invalid"],
        "What industry do you work in?": ["Tech", "Finance", "N/A"],
        "Job title": [" data engineer ", "Analyst", "Unknown"],
        "If your job title needs additional context, please clarify here:": ["", "", ""],
        "What is your annual salary? (You'll indicate the currency in a later question. If you are part-time or hourly, please enter an annualized equivalent -- what you would earn if you worked the job 40 hours a week, 52 weeks a year.)": [
            "$100,000", "85000", "0"],
        "How much additional monetary compensation do you get, if any (for example, bonuses or overtime in an average year)? Please only include monetary compensation here, not the value of benefits.": [
            "5,000", "0", "0"],
        "Please indicate the currency": ["usd", "cad", "USD"],
        "If your income needs additional context, please provide it here:": ["", "", ""],
        "What country do you work in?": ["United States", "Canada", "Mars"],
        "If you're in the U.S., what state do you work in?": ["New York", "", ""],
        "What city do you work in?": ["nyc", "Toronto", ""]
    }
    return pd.DataFrame(data)


def test_clean_standardizes_text(raw_survey_data):
    df = clean(raw_survey_data)

    assert "age" in df.columns

    assert df.iloc[0]["job_title"] == "Data Engineer"
    assert df.iloc[0]["city"] == "Nyc"
    assert df.iloc[0]["currency"] == "USD"
    assert df.iloc[0]["us_state"] == "NY"


def test_salary_cleaning_handles_symbols(raw_survey_data):
    df = clean(raw_survey_data)

    assert df.iloc[0]["salary"] == 100000
    assert isinstance(df.iloc[0]["salary"], (int, float, np.integer, np.floating))


def test_age_cleaning_handles_under_18(raw_survey_data):
    df = clean(raw_survey_data)

    assert df.iloc[0]["age"] == 17
    assert df.iloc[1]["age"] == 45


def test_country_normalization_and_filtering(raw_survey_data):
    df = clean(raw_survey_data)

    assert df.iloc[0]["country"] == "USA"
    assert df.iloc[1]["country"] == "CAN"

    assert len(df) == 2