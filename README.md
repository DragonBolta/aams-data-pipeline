# aams-data-pipeline

A robust ETL data pipeline designed to ingest, clean, validate, and load the results of the annual Ask a Manager salary survey.

The pipeline ensures high data quality by performing comprehensive transformations, schema validation, and dedicated error handling for rejected records.

## 🌟 Features

### 1. Pipeline Architecture & Ingestion
* **Streaming Mode (Primary)**: The primary execution model is a Kafka Consumer that continuously reads single-row JSON messages from a designated Kafka topic. The consumer is fault-tolerant, designed to check for PostgreSQL database readiness and table existence before starting to process messages.

* **Batch Mode (Utility)**: A standalone Python script (src/main.py) remains available for one-off batch processing of local CSV files.

* **Multi-Format Ingestion**: Supports reading data from both CSV (for batch) and JSON (for streaming) sources.

### 2. Robust Data Cleaning
* **Data Normalization**: Converts raw survey fields (like salary and bonus) into clean numeric integers, handles "under 18" age values, and maps categorical years of experience bands (e.g., '5-7 years') to numeric integer values (e.g., 5) for consistent storage.

* **Geographic Standardization**: Normalizes country names to the ISO3 format and standardizes US state names/abbreviations.

* **Demographic Data**: Includes ingestion and cleaning logic for demographic fields like gender, education, race, and yoe.

### 3. Strict Data Validation
* **Great Expectations**: Utilizes Great Expectations for declarative data quality checks.

* **Schema & Business Rules**: 
  
  * Enforces checks for:

      * Non-null values on critical fields, now including job_title, salary, industry, professional_yoe, and industry_yoe.

      * Valid salary and age ranges.

      * Character length restrictions to prevent database truncation, including a specific check for the other_currency field.

### 4. Loading & Error Handling
* **High-Performance Loading**: Loads valid, cleaned data into the target PostgreSQL database using the COPY command via psycopg2's copy_expert.

* **Dedicated Error Table**: All rejected rows (from both the clean and validate steps) are captured and saved to the dedicated salary_errors PostgreSQL table.

* **Error Logging**: Invalid rows are saved as a JSONB payload along with a detailed reason for rejection. The cleaning step captures specific failure reasons, including invalid country codes, missing or invalid timestamps/year, and unmappable YOE values.

## 🛠️ Technology Stack

| Component       | Technology                 | Role                                                   |
|:----------------|:---------------------------|:-------------------------------------------------------|
| Data Processing | Python, Pandas             | Core ETL logic, transformation, and data manipulation  |
| Data Quality    | Great Expectations         | Data validation and quality assurance                  |
| Database        | PostgreSQL, psycopg2       | Target database for storing clean and rejected records |
| Messaging       | Apache Kafka, kafka-python | Decoupled data ingestion and real-time streaming       |
| Libraries       | country_converter, us      | Geographic data standardization                        |

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

### Crucial Note on Dependencies: 

The dependencies listed below are only required if you intend to run the **Batch Mode** script (src/main.py) or **Unit Tests** directly on your host machine for development. The **Streaming Mode (Docker Compose)** uses a container image that has all necessary dependencies already installed.

### 1. Streaming Mode (Docker Compose)

The primary way to run the pipeline is via Docker Compose, which sets up the PostgreSQL database, Kafka broker, and the ETL consumer.

#### Prerequisites

* Docker and Docker Compose must be installed.
    
#### Setup

* Prepare Secrets: Create a file named db_password.txt in the root directory (where docker-compose.yaml is located) and place your desired PostgreSQL password inside.
    
#### Execution

* This will build the ETL consumer image (if necessary) and start the entire stack. The consumer will automatically wait for the database to be ready and create the necessary tables before connecting to Kafka.

  ```bash 
  docker-compose up --build
  ```

### 2. Batch Mode (Local Python)

This is the original execution mode for loading single CSV files directly using a Python environment on your host machine.

#### Prerequisites

* PostgreSQL Server: Must be running and accessible (locally or remotely).

* Python Environment (3.8+).

#### Setup

1. **Install Dependencies**: Create and activate a virtual environment, then install the required Python packages:

```bash
   pip install -r requirements.txt
```

2. **Environment Configuration**: Create a file named .env in the root directory and configure the database connection details:

```
# .env file content (Example values for a local database instance)
POSTGRES_IP=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=secure_password # Placeholder for your password
POSTGRES_DB=salary
POSTGRES_TABLE=salary
```

#### Execution

Place your raw data file (e.g., Ask A Manager Salary Survey 2021 (Responses) - Form Responses 1.csv) into the data/ folder. Run the main script. This will set up the schema and run the ETL once on the specified file:

```bash
# Using the default file path
python src/main.py

# Specifying a custom file path
python src/main.py data/my_custom_survey.csv
```

### 3. Running Tests

Run unit tests using pytest to verify ETL component functionality on your local machine. This requires the local dependencies installed in Step 2.1.

```bash
pytest
```