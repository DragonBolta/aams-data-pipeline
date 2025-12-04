# aams-data-pipeline

A robust ETL data pipeline designed to ingest, clean, validate, and load the results of the annual Ask a Manager salary survey.

The pipeline ensures high data quality by performing comprehensive transformations, schema validation, and dedicated error handling for rejected records.

---

## 🌟 Features

### 1. Robust Data Ingestion & Cleaning
* **Multi-Format Ingestion:** Supports reading data from both CSV and JSON sources.
* **Data Normalization:** Converts raw survey fields (like `salary` and `bonus`) into clean numeric integers by stripping currency symbols and handling "under 18" age values.
* **Geographic Standardization:**
    * Normalizes country names to the ISO3 format using `country_converter`.
    * Standardizes US state names/abbreviations using the `us` library.
* **Demographic Data:** Includes ingestion and cleaning logic for demographic fields like `gender`, `education`, `race`, and `yoe` (Years of Experience).

### 2. Strict Data Validation
* **Great Expectations:** Utilizes Great Expectations for declarative data quality checks.
* **Schema & Business Rules:** Enforces checks for:
    * Non-null values on critical fields like `job_title` and `salary`.
    * Valid salary and age ranges.
    * Character length restrictions to prevent database truncation based on the SQL schema defined in `salary_schema.sql`.

### 3. Loading & Error Handling
* **High-Performance Loading:** Loads valid, cleaned data into the target PostgreSQL database using the `COPY` command via `psycopg2`'s `copy_expert`.
* **Dedicated Error Table:** All rejected rows (from both the `clean` and `validate` steps) are captured and saved to the dedicated `salary_errors` PostgreSQL table.
* **Error Logging:** Invalid rows are saved as a `JSONB` payload along with a detailed `reason` for rejection, enabling easy auditing and debugging.

---

## 🛠️ Technology Stack

| Component | Technology | Role |
| :--- | :--- | :--- |
| **Orchestration** | Apache Airflow, Docker Compose | Scheduled pipeline execution and environment management |
| **Data Processing** | Python, Pandas | Core ETL logic, transformation, and data manipulation |
| **Data Quality** | Great Expectations | Data validation and quality assurance |
| **Database** | PostgreSQL, `psycopg2` | Target database for storing clean and rejected records |
| **Libraries** | `country_converter`, `us` | Geographic data standardization |

---

## 📁 Project Structure
```text
aams-data-pipeline/
├── dags/
│   └── salary_dag.py
│
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
├── docker-compose.yaml
├── requirements.txt
└── .env
```
---

## 🚀 Local Setup and Execution

### Prerequisites

1.  **Docker & Docker Compose:** Required to run the Airflow cluster and PostgreSQL database.
2.  **Python Environment:** For local execution (if not using Docker).

### 1. Environment Configuration

Create a file named `.env` in the root directory to configure the PostgreSQL connection:

```env
# .env file content (Example values matching docker-compose defaults)
PG_IP=postgres
PG_PORT=5432
PG_USER=airflow
PG_PASSWORD=airflow
PG_DB=airflow
```

### 2. Starting the Environment (Airflow)
Start the Airflow and PostgreSQL services using Docker Compose:

docker-compose up -d --build

### 3. Local Script Execution
For a simple, non-orchestrated run:

Place the raw data file (e.g., Ask A Manager Salary Survey 2021 (Responses) - Form Responses 1.csv) into the data/ folder.

Run the main script:

```bash
python src/main.py
```

### 4. Running Tests
Run unit tests:

```bash
pytest
```