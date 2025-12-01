import pytest
from unittest.mock import patch, MagicMock
from src.readers.json_reader import read_json


@patch("src.readers.json_reader.pd.read_json")
@patch("src.readers.json_reader.os.path.exists")
def test_read_json_success(mock_exists, mock_pandas_read):
    """Test successful JSON reading with pandas."""
    mock_exists.return_value = True

    mock_df = MagicMock()
    mock_df.__len__.return_value = 10
    mock_pandas_read.return_value = mock_df

    result = read_json("data/test.json", rows=100)

    assert result == mock_df
    mock_pandas_read.assert_called_once_with("data/test.json", orient='records', lines=True, nrows=100)


@patch("src.readers.json_reader.os.path.exists")
def test_read_json_file_not_found(mock_exists):
    """Test that FileNotFoundError is raised if file doesn't exist."""
    mock_exists.return_value = False

    with pytest.raises(FileNotFoundError):
        read_json("ghost_file.json")


@patch("src.readers.json_reader.pd.read_json")
@patch("src.readers.json_reader.os.path.exists")
def test_read_json_generic_error(mock_exists, mock_pandas_read):
    """Test that generic exceptions are re-raised."""
    mock_exists.return_value = True
    mock_pandas_read.side_effect = Exception("Corrupt JSON file")

    with pytest.raises(Exception) as excinfo:
        read_json("bad.json")

    assert "Corrupt JSON file" in str(excinfo.value)