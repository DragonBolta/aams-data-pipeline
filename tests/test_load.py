import pandas as pd
import os
from unittest.mock import patch, MagicMock, mock_open
from src.load import load_into_db, load_errors, get_secret, setup_db_schema


@patch("builtins.open", new_callable=mock_open, read_data="my_secret_password")
def test_get_secret_success(mock_file):
    result = get_secret("db_password")
    assert result == "my_secret_password"
    mock_file.assert_called_once()


@patch("builtins.open", side_effect=FileNotFoundError())
@patch("builtins.print")
def test_get_secret_file_not_found(mock_print, _):
    result = get_secret("db_password")
    assert result is None
    assert mock_print.called
    call_args = str(mock_print.call_args)
    assert "not found" in call_args


@patch("builtins.open", side_effect=PermissionError("Access denied"))
@patch("builtins.print")
def test_get_secret_general_exception(mock_print, _):
    result = get_secret("db_password")
    assert result is None
    assert mock_print.called
    call_args = str(mock_print.call_args)
    assert "ERROR reading secret" in call_args


@patch("src.load._connect_db")
@patch("builtins.open", new_callable=mock_open, read_data="CREATE TABLE test;")
@patch("src.load.logger")
@patch("os.path.dirname")
@patch("os.path.abspath")
def test_setup_db_schema_success(mock_abspath, mock_dirname, mock_logger, mock_file, mock_connect_db):
    mock_conn = MagicMock()
    mock_conn.closed = False
    mock_cursor = MagicMock()

    mock_connect_db.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

    mock_abspath.return_value = "/fake/path/load.py"
    mock_dirname.return_value = "/fake/path"

    setup_db_schema()

    mock_cursor.execute.assert_called_once()
    mock_logger.info.assert_called_once()
    assert "schema initialized successfully" in str(mock_logger.info.call_args)
    mock_conn.close.assert_called_once()


@patch("src.load._connect_db")
@patch("src.load.logger")
def test_setup_db_schema_connection_failure(mock_logger, mock_connect_db):
    mock_connect_db.side_effect = Exception("Connection failed")

    setup_db_schema()

    mock_logger.exception.assert_called_once()
    assert "schema initialization failed" in str(mock_logger.exception.call_args)


@patch("src.load._connect_db")
@patch("builtins.open", side_effect=FileNotFoundError("Schema file not found"))
@patch("src.load.logger")
@patch("os.path.dirname")
@patch("os.path.abspath")
def test_setup_db_schema_file_not_found(mock_abspath, mock_dirname, mock_logger, mock_file, mock_connect_db):
    mock_conn = MagicMock()
    mock_conn.closed = False

    mock_connect_db.return_value = mock_conn
    mock_abspath.return_value = "/fake/path/load.py"
    mock_dirname.return_value = "/fake/path"

    setup_db_schema()

    mock_logger.exception.assert_called_once()
    mock_conn.rollback.assert_called_once()
    mock_conn.close.assert_called_once()

@patch("src.load.pg.connect")
@patch("src.load.get_secret", return_value="test_password")
def test_get_connection(mock_get_secret, mock_pg_connect):
    mock_conn = MagicMock()
    mock_pg_connect.return_value = mock_conn

    with patch.dict(os.environ, {
        'POSTGRES_IP': 'localhost',
        'POSTGRES_PORT': '5432',
        'POSTGRES_USER': 'testuser',
        'POSTGRES_DB': 'testdb'
    }):
        from src.load import get_connection
        conn = get_connection()

        assert conn.autocommit is False
        assert mock_pg_connect.called

@patch("src.load.get_connection")
@patch("src.load.logger")
def test_load_into_db_empty_logs_warning(mock_logger, mock_get_connection):
    mock_conn = MagicMock()
    mock_conn.closed = False
    mock_cursor = MagicMock()

    mock_get_connection.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

    empty_df = pd.DataFrame(columns=['age', 'salary'])

    load_into_db(empty_df)

    mock_logger.warning.assert_called_once()
    assert "empty" in str(mock_logger.warning.call_args).lower()
    mock_conn.close.assert_called_once()

@patch("src.load.get_connection")
@patch("src.load.logger")
def test_load_errors_empty_logs_info(mock_logger, mock_get_connection):
    mock_conn = MagicMock()
    mock_conn.closed = False

    mock_get_connection.return_value = mock_conn

    empty_df = pd.DataFrame()

    load_errors(empty_df)

    mock_logger.info.assert_called_once()
    assert "No errors to report" in str(mock_logger.info.call_args)
    mock_conn.close.assert_called_once()

@patch("src.load.get_connection")
def test_load_errors_without_drop_reason_column(mock_get_connection):
    mock_conn = MagicMock()
    mock_conn.closed = False
    mock_cursor = MagicMock()
    mock_get_connection.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

    bad_df = pd.DataFrame({
        "age": [1000],
        "salary": [1000]
    })

    load_errors(bad_df, reason="Custom Validation Error")

    assert mock_cursor.executemany.called
    call_args = mock_cursor.executemany.call_args
    data_points = call_args[0][1]

    assert data_points[0][1] == "Custom Validation Error"

    mock_conn.commit.assert_called_once()
    mock_conn.close.assert_called_once()

@patch("src.load.get_connection")
@patch("src.load.logger")
def test_load_into_db_success_logs_info(mock_logger, mock_get_connection):
    mock_conn = MagicMock()
    mock_conn.closed = False
    mock_cursor = MagicMock()

    mock_get_connection.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

    df = pd.DataFrame({
        "age": [30],
        "salary": [100000]
    })

    load_into_db(df)

    info_calls = [call for call in mock_logger.info.call_args_list]
    assert len(info_calls) > 0
    assert "Data loaded successfully" in str(info_calls[-1])

    mock_conn.commit.assert_called_once()
    mock_conn.close.assert_called_once()

@patch("src.load.get_connection")
@patch("src.load.logger")
def test_load_errors_success_logs_info(mock_logger, mock_get_connection):
    mock_conn = MagicMock()
    mock_conn.closed = False
    mock_cursor = MagicMock()
    mock_get_connection.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

    bad_df = pd.DataFrame({
        "age": [1000],
        "salary": [1000],
        "drop_reason": ["Invalid age"]
    })

    load_errors(bad_df)

    info_calls = [call for call in mock_logger.info.call_args_list]
    assert len(info_calls) > 0
    assert "rejected rows" in str(info_calls[-1]).lower()

    mock_conn.commit.assert_called_once()
    mock_conn.close.assert_called_once()