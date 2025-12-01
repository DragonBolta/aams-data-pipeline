import pandas as pd
import pytest
from src.validate import validate

@pytest.fixture
def sample_data():
    return pd.DataFrame({
        "job_title": ["Engineer", None, "Doctor", "Artist", "Nurse"],
        "salary": [100000, 100000, None, 500, 100000],
        "currency": ["USD", "USD", "USD", "USD", "MarsCredits"],
        "age": [30, 30, 30, 30, 30],
        "industry": ["Tech", "Tech", "Tech", "Tech", "Tech"],
        "country": ["USA", "USA", "USA", "USA", "USA"]
    })

def test_validate_splits_rows_correctly(sample_data):
    good_rows, bad_rows = validate(sample_data)

    assert len(good_rows) == 1
    assert good_rows.iloc[0]["job_title"] == "Engineer"

    assert len(bad_rows) == 4
    assert 1 in bad_rows.index
    assert 4 in bad_rows.index