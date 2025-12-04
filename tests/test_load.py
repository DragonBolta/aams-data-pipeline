import pandas as pd
from unittest.mock import patch, MagicMock
from src.load import load_into_db
from src.load import load_errors
import pytest


@patch("src.load.pg.connect")
def test_load_into_db_success(mock_connect):
    mock_conn_instance = MagicMock()
    mock_cursor = MagicMock()

    mock_connect.return_value = mock_conn_instance
    mock_conn_instance.cursor.return_value.__enter__.return_value = mock_cursor

    df = pd.DataFrame({
        "year": [2021],
        "age": [30],
        "industry": ["Tech"],
        "job_title": ["Engineer"],
        "job_context": [""],
        "salary": [100000],
        "bonus": [5000],
        "currency": ["USD"],
        "income_context": [""],
        "country": ["USA"],
        "us_state": ["NY"],
        "city": ["NYC"],
        "professional_yoe": [5],
        "industry_yoe": [5],
        "gender": ["Woman"],
        "education": ["Masters"],
    })

    load_into_db(df)

    assert mock_cursor.execute.called

    call_args = mock_cursor.copy_expert.call_args
    sql_query = call_args[0][0]

    assert "COPY salary" in sql_query
    assert "FROM STDIN" in sql_query

    target_cols = [
        "year",
        "age", "industry", "job_title", "job_context",
        "salary", "bonus", "currency", "income_context",
        "country", "us_state", "city", "professional_yoe",
        "industry_yoe", "gender", "education"
    ]

    assert all(col in sql_query for col in target_cols)

    mock_conn_instance.commit.assert_called_once()

@patch("src.load.pg.connect")
def test_load_skips_empty_dataframe(mock_connect):
    mock_conn = MagicMock()
    mock_connect.return_value = mock_conn
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

    empty_df = pd.DataFrame(columns=['age', 'salary'])

    load_into_db(empty_df)

    mock_cursor.execute.assert_not_called()
    mock_cursor.copy_expert.assert_not_called()
    mock_conn.commit.assert_not_called()


@patch("src.load.pg.connect")
@patch("src.load.logging.getLogger")
def test_load_handles_db_exception(mock_get_logger, mock_connect):
    mock_logger = MagicMock()
    mock_get_logger.return_value = mock_logger

    mock_conn = MagicMock()
    mock_cursor = MagicMock()

    mock_connect.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

    mock_cursor.execute.side_effect = Exception("Database error")

    df = pd.DataFrame({"age": [25], "salary": [50000]})

    load_into_db(df)

    mock_conn.rollback.assert_called_once()
    mock_logger.exception.assert_called_once()


@patch("src.load.pg.connect")
def test_load_errors_success(mock_connect):
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_connect.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

    bad_df = pd.DataFrame({
        "age": [1000, 20],
        "salary": [1000, 2000],
        "drop_reason": ["Failed to clean", "Validation fail"]
    })

    load_errors(bad_df, reason="Test Reason")

    assert mock_cursor.executemany.called
    call_args = mock_cursor.executemany.call_args
    data_points = call_args[0][1]

    assert data_points[0][1] == "Failed to clean"
    assert data_points[1][1] == "Validation fail"

    mock_conn.commit.assert_called_once()


@patch("src.load.pg.connect")
def test_load_errors_skips_empty(mock_connect):
    mock_conn = MagicMock()
    mock_connect.return_value = mock_conn

    empty_df = pd.DataFrame()

    load_errors(empty_df)

    mock_conn.cursor.assert_not_called()
    mock_conn.commit.assert_not_called()


@patch("src.load.pg.connect")
@patch("src.load.logging.getLogger")
def test_load_errors_handles_exception(mock_get_logger, mock_connect):
    mock_logger = MagicMock()
    mock_get_logger.return_value = mock_logger

    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_connect.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

    mock_cursor.executemany.side_effect = Exception("DB Error")

    bad_df = pd.DataFrame({"age": [999]})

    load_errors(bad_df)

    mock_conn.rollback.assert_called_once()
    mock_logger.exception.assert_called_once()