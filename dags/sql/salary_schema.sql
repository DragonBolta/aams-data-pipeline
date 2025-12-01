CREATE TABLE IF NOT EXISTS salary (
    age INT,
    industry varchar(50),
    job_title varchar(100),
    job_context varchar(255),
    salary INT,
    bonus INT,
    currency VARCHAR(7),
    income_text VARCHAR(100),
    country VARCHAR(3),
    us_state VARCHAR(27),
    city varchar(52)
);

CREATE TABLE IF NOT EXISTS salary_errors (
    error_id SERIAL PRIMARY KEY,
    payload JSONB,
    reason TEXT,
    ingestion_time TIMESTAMP DEFAULT NOW()
);