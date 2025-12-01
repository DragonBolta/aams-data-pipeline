import pandas as pd
from unittest.mock import patch, MagicMock
from src.load import load_into_db
from src.load import load_errors


@patch("src.load.pg.connect")  # 1. Stop actual connection
def test_load_into_db_success(mock_connect):
    mock_conn_instance = MagicMock()
    mock_cursor = MagicMock()

    mock_connect.return_value = mock_conn_instance
    mock_conn_instance.cursor.return_value.__enter__.return_value = mock_cursor

    df = pd.DataFrame({
        "age": [30],
        "industry": ["Tech"],
        "salary": [100000],
        "country": ["USA"],
    })


    load_into_db(df)

    assert mock_cursor.execute.called

    call_args = mock_cursor.copy_expert.call_args
    sql_query = call_args[0][0]

    assert "COPY salary" in sql_query
    assert "FROM STDIN" in sql_query

    mock_conn_instance.commit.assert_called_once()

import pandas as pd
from unittest.mock import patch, MagicMock
from src.load import load_into_db

@patch("src.load.pg.connect")
def test_load_skips_empty_dataframe(mock_connect):
    mock_conn = MagicMock()
    mock_connect.return_value = mock_conn

    empty_df = pd.DataFrame()

    load_into_db(empty_df)

    mock_conn.cursor.return_value.__enter__.return_value.execute.assert_not_called()
    mock_conn.cursor.return_value.__enter__.return_value.copy_expert.assert_not_called()

@patch("src.load.pg.connect")
def test_load_handles_db_exception(mock_connect):
    mock_conn = MagicMock()
    mock_cursor = MagicMock()

    mock_connect.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

    mock_cursor.execute.side_effect = Exception("Database error")

    df = pd.DataFrame({"age": [25], "salary": [50000]})

    load_into_db(df)

    mock_conn.rollback.assert_called_once()

@patch("src.load.pg.connect")
def test_load_errors_success(mock_connect):
    """Test that bad rows are inserted into salary_errors table."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_connect.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

    bad_df = pd.DataFrame({
        "age": [1000],
        "salary": ["invalid"]
    })

    load_errors(bad_df, reason="Test Reason")

    assert mock_cursor.executemany.called
    call_args = mock_cursor.executemany.call_args
    sql_query = call_args[0][0]

    assert "INSERT INTO salary_errors" in sql_query
    assert "VALUES (%s, %s)" in sql_query
    mock_conn.commit.assert_called_once()


@patch("src.load.pg.connect")
def test_load_errors_skips_empty(mock_connect):
    """Test that function returns early if dataframe is empty."""
    mock_conn = MagicMock()
    mock_connect.return_value = mock_conn

    empty_df = pd.DataFrame()

    load_errors(empty_df)

    mock_conn.cursor.assert_not_called()


@patch("src.load.pg.connect")
def test_load_errors_handles_exception(mock_connect):
    """Test that DB rollback happens on error."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_connect.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

    mock_cursor.executemany.side_effect = Exception("DB Error")

    bad_df = pd.DataFrame({"age": [999]})

    load_errors(bad_df)

    mock_conn.rollback.assert_called_once()