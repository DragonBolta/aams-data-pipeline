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
        "age", "industry", "job_title", "job_context",
        "salary", "bonus", "currency", "country", "us_state", "city"
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