# Chicago Crime ETL Pipeline

An ETL pipeline that ingests the [Chicago Crimes dataset](https://data.cityofchicago.org/Public-Safety/Crimes-2001-to-Present/ijzp-q8t2) (~8M rows), validates and transforms it, and loads it into a PostgreSQL database. Built as a learning project focusing on engineering standards: structured logging, config management, idempotency and schema validation.

---

## Project Structure

```
chicago_etl/
├── pipeline.py           # Orchestration and ETL logic, loads the DataFrame
├── transform.py     	  # Transformation logic
├── export.py             # Export protocol, sends data to Postgres
├── validate.py           # Validation contracts and DataValidationError
├── config.py             # Config dataclass, loaded from .env
├── queries.py	          # SQL strings as named constants
├── .env.example          # Template — copy to .env and fill in your values
├── chicago_data          # Data folder
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Quickstart

### 1. Clone and install dependencies

```bash
git clone https://github.com/odrive881/chicago-crime-etl1.git
cd chicago-crime-etl1
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
```

Open `.env` and fill in your values:

```env
DB_URL=postgresql://user:password@localhost:5432/crime_database
RAW_FILE_PATH=chicago_data/Crimes_-_2001_to_Present.csv
TARGET_TABLE=crimes
MAX_REJECTION_RATE=0.05
```

### 3. Download the dataset

Download `Crimes_-_2001_to_Present.csv` from the [City of Chicago Open Data Portal](https://data.cityofchicago.org/Public-Safety/Crimes-2001-to-Present/ijzp-q8t2) and place it at the path specified in `RAW_FILE_PATH`.

### 4. Set up the database

Make sure PostgreSQL is running and the database named in your `DB_URL` exists. The pipeline will create the target table automatically on first run.

```bash
createdb chicago_crimes    # if it doesn't exist yet
```

### 5. Run the pipeline

```bash
# Full run: extract -> validate -> transform -> load
python pipeline.py

# Dry run: extract and validate only, no database writes
python pipeline.py --dry-run
```

---

## Pipeline Stages

### Extract

Reads the raw CSV in configurable chunks using `pd.read_csv(..., chunksize=...)` with explicit `dtype` overrides. Only the required columns are loaded. String categoricals are cast to `category`, location and coordinate columns to appropriate numeric types.

### Validate

`validate_raw(df)` in `validate.py` runs all checks before any cleaning or transforming.

Checks performed:
- All required columns are present
- `Date` is within the valid range (2001 – current year)
- `Latitude` / `Longitude` are within Chicago's bounding box (41.6-42.1°N, 87.5-87.9°W)
- `Primary Type` contains no unexpected values beyond a known set
- Null rate per column does not exceed the configured threshold

Raises `AssertionError` with the failure listed if any check fails.

### Transform

Each transformation is a pure function — same input, same output, no side effects. Transformations are applied in order inside `transform(df)`.

| Function | What it does |
|---|---|
| `remove_nulls(df)` | Drops rows missing critical fields |
| `deduplicate(df)` | Removes duplicate `Case Number` rows, keeping first |
| `standardise_text(df)` | Strips whitespace and title-cases string columns |
| `clip_coordinates(df)` | Drops rows outside Chicago's bounding box |
| `add_time_features(df)` | Extracts `year`, `month`, `day_of_week`, `hour`, `is_weekend` |
| `classify_severity(df)` | Maps `Primary Type` to `"violent"`, `"property"`, or `"other"` |

### Load

`load_to_sql(dataframe, engine_function, db_url)` writes to PostgreSQL using SQLAlchemy inside a single transaction. Idempotency is enforced: if the target table already exists with a matching row and column count, the load is skipped and a warning is logged.

`create_summaries(engine, db_url)` materialises three aggregate tables into the same database:

| Table | Description |
|---|---|
| `crimes_by_year_type` | Count and arrest rate by year + primary type |
| `crimes_by_district_month` | Count by district + month |
| `arrest_rate_by_type` | Arrest rate ranked by primary type |

---

## Configuration Reference

All configuration lives in `.env`. No values are hardcoded in the source.

| Variable | Description | Default |
|---|---|---|
| `DB_URL` | SQLAlchemy connection string | — (required) |
| `RAW_FILE_PATH` | Path to the raw CSV file | — (required) |
| `TARGET_TABLE` | PostgreSQL table name for loaded data | `crimes` |
| `MAX_REJECTION_RATE` | Max allowed null rate per column before validation fails | `0.05` |

---

## Logging

All log output is JSON-structured:

```json
{
  "validation": "Complete",
  "time": "2026-07-12 09:58:34"
}{
  "Transformation": "Complete",
  "time": "2026-07-12 09:58:54",
  "nulls dropped": "357824",
  "duplicate dropped": "0",
  "columns standardized": "20",
  "out of bounds": "25932"
}{
  "SUCCESS": {
    "time": "2026-07-12 10:00:25",
    "message": "Dataframe successfully exported to SQL"
  }
}{
  "SUCCESS": {
    "time": "2026-07-12 10:01:56",
    "message": "Summary tables created in Postgres"
  }
}
```

---

## Requirements

```
pandas>=2.0
sqlalchemy>=2.0
psycopg2-binary
python-dotenv
```

Python 3.10+ recommended.
