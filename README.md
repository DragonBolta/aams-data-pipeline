# aams-data-pipeline

A robust ETL data pipeline designed to ingest, clean, validate, and load the results of the annual Ask a Manager salary survey.

The pipeline ensures high data quality by performing comprehensive transformations, schema validation, and dedicated error handling for rejected records.

## 🌟 Features

### 1. Robust Data Ingestion & Cleaning

Multi-Format Ingestion: Supports reading data from both CSV and JSON sources.

Data Normalization: Converts raw survey fields (like salary and bonus) into clean numeric integers by stripping currency symbols and handling "under 18" age values.

Geographic Standardization:

Normalizes country names to the ISO3 format using country_converter.

Standardizes US state names/abbreviations using the us library.

Demographic Data: Includes ingestion and cleaning logic for demographic fields like gender, education, race, and yoe (Years of Experience).

### 2. Strict Data Validation

Great Expectations: Utilizes Great Expectations for declarative data quality checks.

Schema & Business Rules: Enforces checks for:

Non-null values on critical fields like job_title and salary.

Valid salary and age ranges.

Character length restrictions to prevent database truncation based on the SQL schema defined in salary_schema.sql.

### 3. Loading & Error Handling

High-Performance Loading: Loads valid, cleaned data into the target PostgreSQL database using the COPY command via psycopg2's copy_expert.

Dedicated Error Table: All rejected rows (from both the clean and validate steps) are captured and saved to the dedicated salary_errors PostgreSQL table.

Error Logging: Invalid rows are saved as a JSONB payload along with a detailed reason for rejection, enabling easy auditing and debugging.

🛠️ Technology Stack

| Component       | Technology | Role |
|:----------------| :--- | :--- |
| Data Processing | Python, Pandas | Core ETL logic, transformation, and data manipulation |
| Data Quality    | Great Expectations | Data validation and quality assurance |
| Database        | PostgreSQL, psycopg2 | Target database for storing clean and rejected records |
| Libraries       | country_converter, us | Geographic data standardization |

## 📁 Project Structure
```

aams-data-pipeline/
├── sql/
│   └── salary_schema.sql
│
├── src/
│   ├── readers/
│   │   ├── csv_reader.py
│   │   └── json_reader.py
│   │
│   ├── clean.py
│   ├── validate.py
│   ├── load.py
│   └── main.py
│
├── tests/
│   ├── test_clean.py
│   ├── test_validate.py
│   ├── test_load.py
│   └── test_readers.py
│
├── data/
│   └── (place raw CSV/JSON files here)
│
├── requirements.txt
└── .env
```


## 🚀 Local Setup and Execution

### Prerequisites


PostgreSQL Server: Must be running and accessible (locally or remotely).

Python Environment (3.8+): For running the ETL scripts.

### 1. Install Dependencies

Create and activate a virtual environment, then install the required Python packages:

```pip install -r requirements.txt```


### 2. Environment Configuration

Create a file named .env in the root directory and configure the database connection details:

### .env file content (Example values for a local database instance)
PG_IP=localhost
PG_PORT=5432
PG_USER=aams_user
PG_PASSWORD=secure_password
PG_DB=aams_db


### 3. Database Setup

The ETL pipeline is configured to automatically create the necessary salary_data and salary_errors tables on its first execution using the schema defined in sql/salary_schema.sql.

Action Required: Ensure the target database (aams_db in the example above) exists.

### 4. Local Script Execution

Place your raw data file (e.g., Ask A Manager Salary Survey 2021 (Responses) - Form Responses 1.csv) into the data/ folder.

Run the main script. You can use the default file path or specify a custom one:

#### Using the default file path
```python src/main.py```

#### Specifying a custom file path
```python src/main.py data/my_custom_survey.csv```


### 5. Running Tests

Run unit tests using pytest to verify ETL component functionality:

```pytest```
