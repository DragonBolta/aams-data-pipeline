CREATE TABLE IF NOT EXISTS salary (
    year INT,
    age INT,
    industry varchar(50),
    job_title varchar(100),
    job_context varchar(255),
    salary INT,
    bonus INT,
    currency VARCHAR(7),
    other_currency VARCHAR(50),
    income_context VARCHAR(100),
    country VARCHAR(3),
    us_state VARCHAR(27),
    city varchar(52),
    gender varchar(30),
    professional_yoe INT,
    industry_yoe INT,
    education varchar(40),
    race varchar(255)
);

-- CREATE TABLE IF NOT EXISTS countries (
--     country_id INT PRIMARY KEY,
--     country_name INT,
--     country_iso INT
-- );

CREATE TABLE IF NOT EXISTS salary_errors (
    error_id SERIAL PRIMARY KEY,
    payload JSONB,
    reason TEXT,
    ingestion_time TIMESTAMP DEFAULT NOW()
);