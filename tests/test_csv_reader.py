import pytest
from unittest.mock import patch, MagicMock
from src.readers.csv_reader import read_csv

@patch("src.readers.csv_reader.pandas.read_csv")
def test_read_csv_success(mock_pandas_read):
    """Test that read_csv calls pandas correctly."""
    mock_df = MagicMock()
    mock_df.__len__.return_value = 50 # Fake 50 rows
    mock_pandas_read.return_value = mock_df

    result = read_csv("dummy_path.csv", rows=100)

    assert result == mock_df
    mock_pandas_read.assert_called_once_with("dummy_path.csv", nrows=100)