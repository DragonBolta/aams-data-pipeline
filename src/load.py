import logging
import psycopg2 as pg
import os
import io
import json
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


def get_secret(secret_name):
    secret_path = os.path.join('/run/secrets', secret_name)
    try:
        with open(secret_path, 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        logger.exception(f"ERROR: Docker secret '{secret_name}' not found at {secret_path}")
        raise FileNotFoundError
    except Exception as e:
        logger.exception(f"ERROR reading secret '{secret_name}': {e}")
        raise e


pg_ip = os.getenv("POSTGRES_IP")
pg_port = os.getenv("POSTGRES_PORT")
pg_user = os.getenv("POSTGRES_USER")
pg_db = os.getenv("POSTGRES_DB")
pg_pw = None
try:
    pg_pw = get_secret("db_password")
except FileNotFoundError as e:
    logger.info("Failed to get secret, attempting to get database password from environment variables")
if not pg_pw:
    pg_pw = os.getenv("POSTGRES_PASSWORD")


def _connect_db():
    return pg.connect(
        host=pg_ip,
        port=pg_port,
        database=pg_db,
        user=pg_user,
        password=pg_pw,
    )


def setup_db_schema():
    conn = None
    try:
        conn = _connect_db()
        conn.autocommit = True

        current_dir = os.path.dirname(os.path.abspath(__file__))
        schema_path = os.path.join(current_dir, "../dags/sql/salary_schema.sql")

        with conn.cursor() as cur:
            with open(schema_path, "r") as f:
                cur.execute(f.read())
        logger.info("Database schema initialized successfully.")

    except Exception as e:
        logger.exception(f"Database schema initialization failed: {e}")
        if conn and not conn.closed:
            conn.rollback()
    finally:
        if conn and not conn.closed:
            conn.close()


def get_connection():
    conn = _connect_db()
    conn.autocommit = False
    return conn


def load_into_db(df):
    conn = get_connection()

    target_cols = [
        "year",
        "age", "industry", "job_title", "job_context",
        "salary", "bonus", "currency", "income_context",
        "country", "us_state", "city", "professional_yoe",
        "industry_yoe", "gender", "education", "other_currency", "race"
    ]

    valid_cols = [c for c in target_cols if c in df.columns]
    df = df[valid_cols]

    try:
        with conn.cursor() as cur:
            if df.empty:
                logger.warning("Dataframe is empty, skipping load.")
                return

            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False, header=False)
            csv_buffer.seek(0)

            columns = ",".join(valid_cols)
            sql = f"COPY salary ({columns}) FROM STDIN WITH CSV"
            cur.copy_expert(sql, csv_buffer)

            conn.commit()
            logger.info(f"Data loaded successfully. Rows: {len(df)}")

    except Exception as e:
        logger.exception(f"Database load failed: {e}")
        if conn and not conn.closed:
            conn.rollback()
    finally:
        if conn and not conn.closed:
            conn.close()


def _is_valid_value(v):
    """Check if a value is valid for JSON serialization."""
    if pd.isna(v):
        return False
    if isinstance(v, float) and np.isnan(v):
        return False
    if isinstance(v, (float, int)) and not np.isfinite(v):
        return False
    return True


def load_errors(bad_df, reason="Validation Failed"):
    conn = get_connection()

    if bad_df.empty:
        logger.info("No errors to report.")
        if conn and not conn.closed:
            conn.close()
        return

    has_reason_column = 'drop_reason' in bad_df.columns

    try:
        with conn.cursor() as cur:
            temp_df = bad_df.copy(deep=True)

            for col in temp_df.select_dtypes(include=['datetime64', 'datetime64[ns]']).columns:
                temp_df[col] = temp_df[col].astype(str)

            data_values = []
            for row in temp_df.itertuples():
                row_dict = {k: v for k, v in row._asdict().items() if k != 'Index'}

                if has_reason_column:
                    error_reason = row_dict['drop_reason']

                    payload_data = {k: v for k, v in row_dict.items() if k != 'drop_reason'}
                else:
                    error_reason = reason
                    payload_data = row_dict

                cleaned_dict = {}
                for k, v in payload_data.items():
                    try:
                        if _is_valid_value(v):
                            cleaned_dict[k] = str(v)
                        else:
                            cleaned_dict[k] = None
                    except:
                        print(payload_data)

                row_json = json.dumps(cleaned_dict)
                data_values.append((row_json, error_reason))

            insert_query = "INSERT INTO salary_errors (payload, reason) VALUES (%s, %s)"
            cur.executemany(insert_query, data_values)

            conn.commit()
            logger.info(f"Loaded {len(bad_df)} rejected rows into salary_errors table.")

    except Exception as e:
        logger.exception(f"Failed to load errors: {e}")
        if conn and not conn.closed:
            conn.rollback()
    finally:
        if conn and not conn.closed:
            conn.close()