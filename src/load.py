import logging
import psycopg2 as pg
import os
import io
from dotenv import load_dotenv

load_dotenv()

pg_ip = os.getenv("PG_IP")
pg_port = os.getenv("PG_PORT")
pg_user = os.getenv("PG_USER")
pg_pw = os.getenv("PG_PASSWORD")
pg_db = os.getenv("PG_DB")


def get_connection():
    conn = pg.connect(
        host=pg_ip,
        port=pg_port,
        database=pg_db,
        user=pg_user,
        password=pg_pw,
    )
    conn.autocommit = True
    return conn


def load_into_db(df):
    logger = logging.getLogger(__name__)
    conn = get_connection()

    target_cols = [
        "year",
        "age", "industry", "job_title", "job_context",
        "salary", "bonus", "currency", "income_context",
        "country", "us_state", "city", "professional_yoe",
        "industry_yoe", "gender", "education"
    ]

    valid_cols = [c for c in target_cols if c in df.columns]
    df = df[valid_cols]

    current_dir = os.path.dirname(os.path.abspath(__file__))
    schema_path = os.path.join(current_dir, "../dags/sql/salary_schema.sql")

    try:
        with conn.cursor() as cur:
            if df.empty:
                logger.warning("Dataframe is empty, skipping load.")
                return

            with open(schema_path, "r") as f:
                cur.execute(f.read())

            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False, header=False)
            csv_buffer.seek(0)

            columns = ",".join(valid_cols)
            sql = f"COPY salary ({columns}) FROM STDIN WITH CSV"
            cur.copy_expert(sql, csv_buffer)

            conn.commit()
            logger.info("Data loaded successfully.")

    except Exception as e:
        logger.exception(f"Database load failed: {e}")
        conn.rollback()
    finally:
        conn.close()


def load_errors(bad_df, reason="Validation Failed"):
    logger = logging.getLogger(__name__)
    conn = get_connection()

    if bad_df.empty:
        logger.info("No errors to report.")
        conn.close()
        return

    has_reason_column = 'drop_reason' in bad_df.columns

    try:
        with conn.cursor() as cur:
            data_values = []

            for _, row in bad_df.iterrows():
                if has_reason_column:
                    error_reason = row['drop_reason']
                    payload_data = row.drop(labels=['drop_reason'])
                else:
                    error_reason = reason
                    payload_data = row

                row_json = payload_data.to_json()
                data_values.append((row_json, error_reason))

            insert_query = "INSERT INTO salary_errors (payload, reason) VALUES (%s, %s)"
            cur.executemany(insert_query, data_values)

            conn.commit()
            logger.info(f"Loaded {len(bad_df)} rejected rows into salary_errors table.")

    except Exception as e:
        logger.exception(f"Failed to load errors: {e}")
        conn.rollback()
    finally:
        conn.close()